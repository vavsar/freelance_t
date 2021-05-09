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
TITLE = 'test_title'
TEXT = 'test_text'
TASK_PRICE = 200
START_BALANCE = 500
TASKS_LIST_URL = reverse('tasks-list')
TASK_NEW_DATA = {'title': 'test_title2',
                 'text': '2222',
                 'price': TASK_PRICE}
RESPOND_NEW_DATA = {'author': 2, 'task': 1}


class TaskModelTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username=AUTHOR,
            email=AUTHOR_EMAIL,
            balance=START_BALANCE,
            freeze_balance=START_BALANCE,
            role=AUTHOR_ROLE)
        cls.executor = User.objects.create_user(
            username=EXECUTOR,
            email=EXECUTOR_EMAIL,
            balance=START_BALANCE,
            freeze_balance=START_BALANCE,
            role=EXECUTOR_ROLE)
        cls.task1 = Task.objects.create(
            author=cls.author,
            title=TITLE,
            price=TASK_PRICE,
            status='active')
        cls.executor_client = APIClient()
        cls.executor_client.force_authenticate(user=cls.executor)
        cls.token = RefreshToken.for_user(cls.author)
        cls.author_token = cls.token.access_token
        cls.auth_client = APIClient()
        cls.auth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {cls.author_token}')
        cls.TASK_DETAIL_URL = reverse('tasks-detail', args=[cls.task1.id])

    def test_get_tasks_list(self):
        response = self.auth_client.get(TASKS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(self.task1.title, response.json()['results'][0]['title'])

    def test_get_task_detail(self):
        response = self.auth_client.get(self.TASK_DETAIL_URL)
        serializer_data = TasksSerializer(self.task1).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer_data, response.data)

    def test_author_create_task(self):
        response = self.auth_client.post(
            TASKS_LIST_URL,
            data=json.dumps(TASK_NEW_DATA),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        task = Task.objects.exclude(id=self.task1.id)[0]
        self.assertEqual(task.author, self.author)
        self.assertEqual(task.title, response.json()['title'])
        self.assertEqual(task.status, response.json()['status'])

    def test_executor_cant_create_task(self):
        response = self.executor_client.post(
            TASKS_LIST_URL,
            data=json.dumps(TASK_NEW_DATA),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_edit_task(self):
        tasks = Task.objects.count()
        response = self.auth_client.patch(
            self.TASK_DETAIL_URL,
            data=json.dumps(TASK_NEW_DATA),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(tasks, 1)
        self.assertEqual(response.json()['title'], 'test_title2')
        self.assertEqual(response.json()['text'], '2222')

    def test_executor_cant_edit_task(self):
        new_data = TASK_NEW_DATA
        response = self.executor_client.patch(
            self.TASK_DETAIL_URL,
            data=json.dumps(new_data),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_task(self):
        tasks_before = Task.objects.count()
        response = self.auth_client.delete(self.TASK_DETAIL_URL)
        tasks_after = Task.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(tasks_before, tasks_after + 1)

    def test_executor_cant_delete_task(self):
        tasks_before = Task.objects.count()
        response = self.executor_client.delete(self.TASK_DETAIL_URL)
        tasks_after = Task.objects.count()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(tasks_before, tasks_after)

    def test_create_task_freeze_balance(self):
        balance_before = self.task1.author.balance
        freeze_balance_before = self.task1.author.freeze_balance
        response = self.auth_client.post(
            TASKS_LIST_URL,
            data=json.dumps(TASK_NEW_DATA),
            content_type='application/json')
        task = Task.objects.exclude(id=self.task1.id)[0]
        self.assertEqual(self.task1.author, task.author)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(balance_before, task.author.balance + TASK_PRICE)
        self.assertEqual(freeze_balance_before, task.author.freeze_balance - TASK_PRICE)

    def test_cant_create_task_if_balance_lt_task_price(self):
        tasks_count = Task.objects.count()
        response = self.auth_client.post(
            TASKS_LIST_URL,
            data=json.dumps({'title': 'test_title2',
                             'text': '2222',
                             'price': START_BALANCE+200}),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(tasks_count, Task.objects.count())

    def test_cant_make_status_DONE_if_executor_not_chosen(self):
        response = self.auth_client.patch(
            self.TASK_DETAIL_URL,
            data=json.dumps({'status': 'done'}),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.task1.status, 'active')

    def test_can_make_status_DONE_if_executor_chosen(self):
        task2 = Task.objects.create(
            author=self.author,
            executor=self.executor,
            title=TITLE,
            price=TASK_PRICE,
            status='active'
        )
        response = self.auth_client.patch(
            reverse('tasks-detail', args=[task2.id]),
            data=json.dumps({'status': 'done'}),
            content_type='application/json')
        task2.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(task2.status, 'done')

    def test_DONE_status_moves_money_from_freeze_bal_to_executor_balance(self):
        task2 = Task.objects.create(
            author=self.author,
            executor=self.executor,
            title=TITLE,
            price=100,
            status='active'
        )
        author_balance_before = task2.author.freeze_balance
        self.auth_client.patch(
            reverse('tasks-detail', args=[task2.id]),
            data=json.dumps({'status': 'done'}),
            content_type='application/json')
        task2.refresh_from_db()
        author_balance_after = task2.author.freeze_balance
        self.assertEqual(author_balance_before, author_balance_after + task2.price)
        self.assertEqual(task2.executor.balance, START_BALANCE + task2.price)

    def test_cant_pay_more_than_once_per_task(self):
        task2 = Task.objects.create(
            author=self.author,
            executor=self.executor,
            title=TITLE,
            price=TASK_PRICE,
            status='done'
        )
        author_balance_before = task2.author.freeze_balance
        self.auth_client.patch(
            reverse('tasks-detail', args=[task2.id]),
            data=json.dumps({'status': 'active'}),
            content_type='application/json')
        self.auth_client.patch(
            reverse('tasks-detail', args=[task2.id]),
            data=json.dumps({'status': 'done'}),
            content_type='application/json')
        task2.refresh_from_db()
        author_balance_after = task2.author.freeze_balance
        self.assertEqual(author_balance_before, author_balance_after)
        self.assertEqual(task2.executor.balance, START_BALANCE)

    # def test_cant_pay_if_no_money_on_balance(self):
    #     task2 = Task.objects.create(
    #         author=self.author,
    #         executor=self.executor,
    #         title=TITLE,
    #         price=1000,
    #         status='active'
    #     )
    #     author_balance_before = task2.author.freeze_balance
    #     self.auth_client.patch(
    #         reverse('tasks-detail', args=[task2.id]),
    #         data=json.dumps({'status': 'done'}),
    #         content_type='application/json')
    #     task2.refresh_from_db()
    #     author_balance_after = task2.author.freeze_balance
    #     print(author_balance_before)
    #     print(author_balance_after)
    #     self.assertEqual(author_balance_before, author_balance_after+task2.price)
    # self.assertEqual(task2.executor.balance, START_BALANCE+task2.price)


class RespondTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username=AUTHOR,
            email=AUTHOR_EMAIL,
            role=AUTHOR_ROLE)
        cls.executor = User.objects.create_user(
            username=EXECUTOR,
            email=EXECUTOR_EMAIL,
            role=EXECUTOR_ROLE)
        cls.task1 = Task.objects.create(
            author=cls.author,
            title=TITLE,
            text=TEXT,
            status='active')
        cls.respond1 = Respond.objects.create(
            author=cls.executor,
            task=cls.task1)
        cls.executor_client = APIClient()
        cls.executor_client.force_authenticate(user=cls.executor)
        cls.auth_client = APIClient()
        cls.auth_client.force_authenticate(user=cls.author)
        cls.TASK_DETAIL_URL = reverse('tasks-detail', args=[cls.task1.id])
        cls.RESPONDS_LIST_URL = reverse('respond-list', args=[cls.task1.id])
        cls.RESPOND_DETAIL_URL = reverse('respond-detail',
                                         args=[cls.task1.id,
                                               cls.respond1.id])
        cls.RESPOND_WINNER = reverse('respond-winner',
                                     args=[cls.task1.id,
                                           cls.respond1.id])

    def test_get_responds_list(self):
        data = {'id': 1,
                'author': 2,
                'task': 1}
        response = self.auth_client.get(self.RESPONDS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(data in response.json().get('results'))

    def test_get_responds_detail(self):
        response = self.auth_client.get(self.RESPOND_DETAIL_URL)
        serializer_data = RespondsSerializer(self.respond1).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer_data, response.data)

    def test_executor_create_respond(self):
        response = self.executor_client.post(
            self.RESPONDS_LIST_URL,
            data=json.dumps(RESPOND_NEW_DATA),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Respond.objects.count(), 2)
        respond = Respond.objects.exclude(id=self.respond1.id)[0]
        self.assertEqual(respond.id, 2)
        self.assertEqual(respond.author.id, response.json()['author'])
        self.assertEqual(respond.task.id, response.json()['task'])

    def test_author_cant_create_respond(self):
        response = self.auth_client.post(
            self.RESPONDS_LIST_URL,
            data=json.dumps(RESPOND_NEW_DATA),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Respond.objects.count(), 1)

    def test_executor_can_delete_respond(self):
        responds_before = Respond.objects.count()
        response = self.executor_client.delete(self.RESPOND_DETAIL_URL)
        responds_after = Respond.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(responds_before, responds_after + 1)

    def test_author_cant_delete_respond(self):
        responds_before = Respond.objects.count()
        response = self.auth_client.delete(self.RESPOND_DETAIL_URL)
        responds_after = Respond.objects.count()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(responds_before, responds_after)

    def test_author_choose_winner(self):
        data = {}
        response = self.auth_client.patch(
            self.RESPOND_WINNER,
            data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['executor'], self.respond1.author.id)

    def test_executor_cant_choose_winner(self):
        data = {}
        response = self.executor_client.patch(
            self.RESPOND_WINNER,
            data=data,
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TransactionsTest(APITestCase):
    pass
