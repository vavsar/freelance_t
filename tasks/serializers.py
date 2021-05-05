from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Task, Respond

User = get_user_model()


class TasksSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    executor = serializers.SlugRelatedField(
        default=serializers.CreateOnlyDefault(None),
        slug_field='username',
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Task
        fields = '__all__'


class RespondsSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='id',
        read_only=True
    )
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )

    class Meta:
        model = Respond
        fields = '__all__'
