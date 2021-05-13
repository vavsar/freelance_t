from django.contrib import admin

from .models import Task, Respond, Transaction, Comment


class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'executor',
        'title',
        'text',
        'status',
        'price'
    )
    list_editable = ('status',)


class RespondAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'task',
    )


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'task',
        'author',
        'executor',
        'price',
        'status',
    )


admin.site.register(Task, TaskAdmin)
admin.site.register(Comment)
admin.site.register(Respond, RespondAdmin)
admin.site.register(Transaction, TransactionAdmin)
