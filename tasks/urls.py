from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import TasksViewSet, RespondViewSet

router_v1 = DefaultRouter()
router_v1.register('', TasksViewSet, basename='tasks')
router_v1.register(r'(?P<task_id>\d+)/respond',
                   RespondViewSet,
                   basename='respond')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
