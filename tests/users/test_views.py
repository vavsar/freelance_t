import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from tasks.models import Task, Respond
from tasks.serializers import TasksSerializer, RespondsSerializer

User = get_user_model()

AUTHOR = 'author'
EXECUTOR = 'executor'
AUTHOR_EMAIL = 'author@gmail.com'
EXECUTOR_EMAIL = 'executor@gmail.com'
AUTHOR_ROLE = 'author'
EXECUTOR_ROLE = 'executor'
START_BALANCE = 500
NEW_BALANCE = 1
USERS_LIST_URL = reverse('users-list')
RESPOND_NEW_DATA = {'author': 2, 'task': 1}


class TaskModelTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@gmail.com',
            balance=START_BALANCE,
            freeze_balance=START_BALANCE,
            is_staff=True,
            is_superuser=True)
        self.author = User.objects.create_user(
            username=AUTHOR,
            email=AUTHOR_EMAIL,
            balance=START_BALANCE,
            freeze_balance=START_BALANCE,
            role=AUTHOR_ROLE)
        self.executor = User.objects.create_user(
            username=EXECUTOR,
            email=EXECUTOR_EMAIL,
            balance=START_BALANCE,
            freeze_balance=START_BALANCE,
            role=EXECUTOR_ROLE)
        self.ADMIN_DETAIL_URL = reverse('users-detail', args=[self.admin.id])
        self.AUTHOR_DETAIL_URL = reverse('users-detail', args=[self.author.id])
        self.EXECUTOR_DETAIL_URL = reverse('users-detail', args=[self.executor.id])
        self.executor_client = APIClient()
        self.executor_client.force_authenticate(user=self.executor)
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        self.token = RefreshToken.for_user(self.author)
        self.author_token = self.token.access_token
        self.auth_client = APIClient()
        self.auth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

    def test_admin_get_users_list(self):
        response = self.admin_client.get(USERS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_not_admin_cant_get_users_list(self):
        response = self.auth_client.get(USERS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_user_data(self):
        balance_before = self.author.balance
        response = self.admin_client.patch(
            self.AUTHOR_DETAIL_URL,
            data=json.dumps({'balance': NEW_BALANCE}),
            content_type='application/json')
        self.author.refresh_from_db()
        balance_after = self.author.balance
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(balance_before, START_BALANCE)
        self.assertEqual(balance_after, NEW_BALANCE)

    def test_not_admin_cant_update_user_data(self):
        balance_before = self.author.balance
        response = self.auth_client.patch(
            self.AUTHOR_DETAIL_URL,
            data=json.dumps({'balance': NEW_BALANCE}),
            content_type='application/json')
        self.author.refresh_from_db()
        balance_after = self.author.balance
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(balance_before, balance_after)
