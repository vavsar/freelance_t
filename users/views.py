from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from freelance1.settings import NOREPLY_FREELANCE1_EMAIL
from users.serializers import EmailSerializer, CodeSerializer, UserSerializer, BalanceSerializer

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    permission_classes = (IsAdminUser,)

    @action(detail=False,
            methods=['get', 'patch'],
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        user = get_object_or_404(User, id=request.user.id)
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=user.role, balance=user.balance,
                        freeze_balance=user.freeze_balance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['patch'],
            permission_classes=(IsAuthenticated,))
    def balance(self, request):
        user = get_object_or_404(User, id=request.user.id)
        serializer = BalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.balance += Decimal(serializer.data['balance'])
        user.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmailConfirm(viewsets.ViewSet):
    @action(detail=False,
            methods=['post'],
            url_path='email')
    def send_confirmation_code(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, create = User.objects.get_or_create(
            username=serializer.data['username'],
            email=serializer.data['email'],
            role=serializer.data['role'],
        )
        token = default_token_generator.make_token(user)
        mail_subject = 'Confirmation code'
        message = f'Используйте этот код для получения доступа: {token}'
        send_mail(mail_subject,
                  message,
                  NOREPLY_FREELANCE1_EMAIL,
                  [user.email]
                  )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['post'],
            url_path='token')
    def token_obtain(self, request):
        serializer = CodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, email=serializer.data['email'])
        code = serializer.data['confirmation_code']
        if default_token_generator.check_token(user, code):
            token = RefreshToken.for_user(user)
            return Response({'token': f'{token.access_token}'},
                            status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
