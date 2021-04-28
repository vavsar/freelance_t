from django.db import models
from django.contrib.auth.models import AbstractUser


class UserRole(models.TextChoices):
    AUTHOR = 'author'
    EXECUTOR = 'executor'


class User(AbstractUser):
    first_name = models.CharField('Имя', max_length=30, blank=True)
    last_name = models.CharField('Фамилия', max_length=30, blank=True)
    username = models.CharField('Имя пользователя', max_length=25, unique=True)
    email = models.EmailField('email', unique=True)
    phone = models.CharField('телефон', unique=True, max_length=11)
    role = models.CharField(
        max_length=15,
        choices=UserRole.choices,
        default=UserRole.EXECUTOR,
    )
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'email']

    @property
    def is_client(self):
        return self.role == UserRole.AUTHOR

    @property
    def is_executor(self):
        return self.role == UserRole.EXECUTOR

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        abstract = True
