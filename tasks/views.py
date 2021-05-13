from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.response import Response

from .helpers import TransactionCreation
from .models import Task, Respond, Comment
from .permissions import IsAuthor, IsExecutor
from .serializers import TasksSerializer, RespondsSerializer, CommentSerializer, CreateCommentSerializer

User = get_user_model()


class TasksViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthor,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        executor=None)


class CommentsViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return CommentSerializer
        return CreateCommentSerializer

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        return task.comments.filter(parent=None)

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task)


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
        transaction_log = TransactionCreation(task)
        if task.executor is not None:
            transaction_log.create_transaction_fail(task.executor)
            return Response(f'Executor is already chosen: {task.executor}')
        task.executor = respond.author
        task.status = 'in_progress'
        serializer = TasksSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
