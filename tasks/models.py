from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TaskStatuses(models.TextChoices):
    ACTIVE = 'active'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    ABANDONED = 'abandoned'


class Task(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='task_authors', verbose_name='Author')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=True, related_name='task_executors',
                                 default=None,
                                 verbose_name='Executor')
    title = models.CharField('Title', max_length=30)
    text = models.TextField('Text', default='', null=True)
    status = models.CharField(
        max_length=15,
        choices=TaskStatuses.choices,
        default=TaskStatuses.ACTIVE,
    )
    price = models.DecimalField(default=500, max_digits=10, decimal_places=0)

    def __str__(self):
        return self.title


class Respond(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='responds')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='responds')


class Transaction(models.Model):
    SUCCESS = 'Success'
    FAIL = 'Fail'
    STATUS_CHOICES = (
        (SUCCESS, 'Success'),
        (FAIL, 'Fail')
    )
    created = models.DateTimeField(auto_now=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='transactions')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='transactions_author')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=True,
                                 related_name='transactions_executor')
    price = models.DecimalField(default=0, max_digits=10, decimal_places=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
