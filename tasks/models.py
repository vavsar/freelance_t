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
                                 verbose_name='Executor')
    title = models.CharField('Title', max_length=30)
    text = models.TextField('Text', default='')
    status = models.CharField(
        max_length=15,
        choices=TaskStatuses.choices,
        default=TaskStatuses.ACTIVE,
    )


class Respond(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='responds')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='responds')
