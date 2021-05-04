from django.contrib.auth import get_user_model
from django.test import TestCase
from tasks.models import Task

User = get_user_model()

AUTHOR = 'author'
EXECUTOR = 'executor'
AUTHOR_EMAIL = 'author@gmail.com'
EXECUTOR_EMAIL = 'executor@gmail.com'
AUTHOR_ROLE = 'author'
EXECUTOR_ROLE = 'executor'
TITLE = 'test_title'


class TaskModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.executor = User.objects.create(username=EXECUTOR,
                                   email=EXECUTOR_EMAIL,
                                   role=EXECUTOR_ROLE)
        cls.author = User.objects.create(username=AUTHOR,
                                       email=AUTHOR_EMAIL,
                                       role=AUTHOR_ROLE)
        cls.task = Task.objects.create(author=cls.author, title=TITLE)

    def test_task_title_label(self):
        task = self.task
        fields_verboses = {
            'author': 'Author',
            'executor': 'Executor',
            'title': 'Title',
            'text': 'Text',
        }
        for value, expected in fields_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).verbose_name, expected)

    def test_task_default_status(self):
        status = self.task.status
        self.assertEqual(status, 'active')
