from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from .models import Task
from .permissions import IsAuthor, IsExecutor
from .serializers import TasksSerializer, RespondsSerializer

User = get_user_model()


class TasksViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TasksSerializer
    permission_classes = (IsAuthor,)

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
