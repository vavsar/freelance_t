from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .exceptions import BalanceTransferError
from .helpers import TransactionCreation
from .models import Task, Respond, Comment

User = get_user_model()

DONE = 'done'


class RecursiveSerializer(serializers.Serializer):
    """Вывод рекурсивно children"""
    def to_representation(self, value):
        serializer = CommentSerializer(value, context=self.context)
        return serializer.data


class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    children = RecursiveSerializer(many=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'task', 'parent', 'children')


class TasksSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    comments = CommentSerializer(many=True)

    def create(self, validated_data):
        request = self.context['request']
        if validated_data['price'] > request.user.balance:
            raise serializers.ValidationError(
                'Not enough money on your balance')
        task_price = validated_data['price']
        instance = Task.objects.select_for_update().create(**validated_data)
        transaction_log = TransactionCreation(instance)
        try:
            with transaction.atomic():
                instance.author.balance -= task_price
                instance.author.freeze_balance += task_price
                instance.author.save()
                transaction_log.create_transaction_success()
        except BalanceTransferError:
            transaction_log.create_transaction_fail()
        return instance

    def update(self, instance, validated_data):
        transaction_log = TransactionCreation(instance)
        if instance.status == DONE:
            raise serializers.ValidationError('Task is already done')
        elif validated_data.get('status') != DONE:
            instance.author = validated_data.get('author', instance.author)
            instance.executor = validated_data.get('executor',
                                                   instance.executor)
            instance.title = validated_data.get('title', instance.title)
            instance.text = validated_data.get('text', instance.text)
            instance.price = validated_data.get('price', instance.price)
            instance.save()
        elif (instance.executor is None and
              validated_data.get('status') == DONE):
            transaction_log.create_transaction_fail()
            raise serializers.ValidationError(
                'Choose executor before making status DONE')
        elif (instance.executor is not None and
              validated_data.get('status') == DONE):
            try:
                with transaction.atomic():
                    instance.status = validated_data.get('status',
                                                         instance.status)
                    instance.author.freeze_balance -= instance.price
                    instance.executor.balance += instance.price
                    instance.author.save()
                    instance.executor.save()
                    instance.save()
                    transaction_log.create_transaction_success(
                        instance.executor)
            except BalanceTransferError:
                transaction_log.create_transaction_fail(instance.executor)
        return instance

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
