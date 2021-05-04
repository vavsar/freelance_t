from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from tasks.models import Task
from tasks.serializers import TasksSerializer

User = get_user_model()

AUTHOR = 'author'
AUTHOR2 = 'author2'
EXECUTOR = 'executor'
AUTHOR_EMAIL = 'author@gmail.com'
EXECUTOR_EMAIL = 'executor@gmail.com'
AUTHOR_ROLE = 'author'
EXECUTOR_ROLE = 'executor'
TITLE = 'test_title'


class TaskModelTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username=AUTHOR,
                                         email='1@gmail.com',
                                         role=AUTHOR_ROLE)
        cls.task1 = Task.objects.create(author=cls.author,
                                        title=TITLE,
                                        status='active')
        cls.data = {'id': 1,
                    'author': 'author',
                    'executor': None,
                    'title': 'test_title',
                    'text': '',
                    'status': 'active'}
        client = APIClient()
        client.force_authenticate(user=cls.author)

    def test_get_tasks_list(self):
        response = self.client.get(reverse('tasks-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(self.data in response.json().get('results'))

    def test_get_task_detail(self):
        response = self.client.get(reverse('tasks-detail', args=[self.task1.id]))
        serializer_data = TasksSerializer(self.task1).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer_data, response.data)
