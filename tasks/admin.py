from django.contrib import admin

from .models import Task


class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'executor',
        'title',
        'text',
    )


admin.site.register(Task, TaskAdmin)
