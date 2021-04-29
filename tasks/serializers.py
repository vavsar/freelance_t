from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Task

User = get_user_model()


class TasksSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all()
    )
    executor = serializers.SlugRelatedField(
        default=serializers.CreateOnlyDefault(None),
        slug_field='username',
        queryset=User.objects.all()
    )

    class Meta:
        model = Task
        fields = '__all__'
