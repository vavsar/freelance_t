from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .exceptions import BalanceTransferError
from .helpers import TransactionCreation
from .models import Task, Respond
from .permissions import IsAuthor, IsExecutor
from .serializers import TasksSerializer, RespondsSerializer

User = get_user_model()


class TasksViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthor,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['price'] > request.user.balance:
            return Response('Not enough money on your balance',
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        task = get_object_or_404(Task, id=serializer.data['id'])
        if not task:
            return Response('Something went wrong by creating Task',
                            status=status.HTTP_400_BAD_REQUEST)
        make_transaction = TransactionCreation(task, task.author, task.price)
        try:
            user = get_object_or_404(User, id=task.author.id)
            with transaction.atomic():
                user.balance -= task.price
                user.freeze_balance += task.price
                user.save()
                make_transaction.create_transaction_success()
        except BalanceTransferError:
            make_transaction.create_transaction_fail()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        executor=None)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        make_transaction = TransactionCreation(instance, instance.author, instance.price)
        if (instance.status != 'done' and
                serializer.validated_data.get('status') != 'done'):
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif (instance.status != 'done' and
              instance.executor is None and
              serializer.validated_data.get('status') == 'done'):
            return Response('Choose executor before making status DONE',
                            status=status.HTTP_400_BAD_REQUEST)
        elif instance.status == 'done':
            return Response(serializer.data, status=status.HTTP_200_OK)
        try:
            with transaction.atomic():
                instance.author.freeze_balance -= instance.price
                instance.executor.balance += instance.price
                instance.author.save()
                instance.executor.save()
                make_transaction.create_transaction_success(instance.executor)
        except BalanceTransferError:
            make_transaction.create_transaction_fail(instance.executor)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RespondViewSet(viewsets.ModelViewSet):
    serializer_class = RespondsSerializer
    permission_classes = (IsExecutor,)

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        return task.responds.all()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(author=self.request.user, task=task)

    @action(detail=False,
            methods=['patch'],
            permission_classes=(IsAuthor,),
            url_path=r'(?P<respond_id>\d+)/winner')
    def winner(self, request, **kwargs):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        respond = get_object_or_404(Respond, pk=self.kwargs.get('respond_id'))
        task_data = TasksSerializer(task).data
        transact = TransactionCreation(task, task.author, task.price)
        if task_data['executor'] is not None:
            transact.create_transaction_fail(task.executor)
            return Response(f'Winner is already chosen: {task.executor}')
        task_data['executor'] = respond.author.id
        task_data['status'] = 'in_progress'
        serializer = TasksSerializer(task, data=task_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
