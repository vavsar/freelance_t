from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import Task, Respond, Transaction
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
        self.perform_create(serializer)
        task = get_object_or_404(Task, id=serializer.data['id'])
        with transaction.atomic():
            Transaction.objects.create(task=task,
                                       author=task.author,
                                       price=task.price,
                                       status='success'
                                       )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        executor=None)


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
        task_data['executor'] = respond.author
        # task_data['status'] = 'in_progress'
        serializer = TasksSerializer(task, data=task_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
