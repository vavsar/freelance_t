from django.contrib import admin

from .models import Task, Respond


class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'executor',
        'title',
        'text',
        'status'
    )


class RespondAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'task',
    )


admin.site.register(Task, TaskAdmin)
admin.site.register(Respond, RespondAdmin)
