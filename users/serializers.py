from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username',
                  'email', 'role', 'balance', 'freeze_balance')


class EmailSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=True)
    role = serializers.CharField(max_length=10)

    class Meta:
        fields = ('username', 'email', 'role')


class CodeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    confirmation_code = serializers.CharField(required=True)
