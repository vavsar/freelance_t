from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import EmailConfirm, UsersViewSet

router_v1 = DefaultRouter()
router_v1.register('users', UsersViewSet, basename='users')
router_v1.register('auth', EmailConfirm, basename='emailconfirm')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
