from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Task(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='task_author')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 default='', null=True,
                                 related_name='task_executor')
    title = models.CharField(max_length=30)
    text = models.TextField()
