from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .exceptions import BalanceTransferError
from .models import Task, Respond, Transaction
from .permissions import IsAuthor, IsExecutor
from .serializers import TasksSerializer, RespondsSerializer

User = get_user_model()


class TransactionCreation:
    def __init__(self, task, author, price, executor=None):
        self.task = task
        self.author = author
        self.price = price
        self.executor = executor

    def create_transaction_success(self, executor=None):
        Transaction.objects.create(
            task=self.task,
            author=self.task.author,
            price=self.task.price,
            executor=executor,
            status='Success')

    def create_transaction_fail(self, executor=None):
        Transaction.objects.create(
            task=self.task,
            author=self.task.author,
            price=self.task.price,
            executor=executor,
            status='Fail')


class TasksViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthor,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        task = get_object_or_404(Task, id=serializer.data['id'])
        if task:
            transact = TransactionCreation(task, task.author, task.price)
            try:
                user = get_object_or_404(User, id=task.author.id)
                user.balance -= task.price
                user.freeze_balance += task.price
                user.save()
                with transaction.atomic():
                    transact.create_transaction_success()
            except BalanceTransferError:
                transact.create_transaction_fail()
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
        transact = TransactionCreation(instance, instance.author, instance.price)
        if (not instance.status == 'done' and
                not serializer.validated_data.get('status') == 'done'):
            self.perform_update(serializer)
            return Response(serializer.data)
        elif (not instance.status == 'done' and
              instance.executor is None and
              serializer.validated_data.get('status') == 'done'):
            return Response('Choose executor before making status DONE',
                            status=status.HTTP_400_BAD_REQUEST)
        elif (not instance.status == 'done' and
              instance.executor is not None):
            try:
                with transaction.atomic():
                    instance.author.freeze_balance -= instance.price
                    instance.executor.balance += instance.price
                    instance.author.save()
                    instance.executor.save()
                    transact.create_transaction_success(instance.executor)
            except BalanceTransferError:
                transact.create_transaction_fail(instance.executor)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()


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
