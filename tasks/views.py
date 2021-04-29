from django.contrib.auth import get_user_model
from rest_framework import viewsets

from .models import Task
from .serializers import TasksSerializer

User = get_user_model()


class TasksViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TasksSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        executor=None)
