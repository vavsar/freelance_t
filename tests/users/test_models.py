from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()

EXECUTOR = 'executor'
EXECUTOR_EMAIL = 'executor@gmail.com'
AUTHOR_ROLE = 'author'
EXECUTOR_ROLE = 'executor'
TITLE = 'test_title'


class UserModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(first_name='asdf',
                                       last_name='fdsa',
                                       username=EXECUTOR,
                                       email=EXECUTOR_EMAIL,
                                       role=EXECUTOR_ROLE)

    def test_user_label(self):
        user = self.user
        fields_verboses = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'email',
            'username': 'Username',
        }
        for value, expected in fields_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    user._meta.get_field(value).verbose_name, expected)

    def test_user_default_role(self):
        role = self.user.role
        self.assertEqual(role, 'executor')

    def test_task_str(self):
        user = self.user
        self.assertEquals(str(user), user.username)
