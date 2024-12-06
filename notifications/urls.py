from django.contrib import admin
from django.urls import path
from .views import NotificationsIndex, reset_notifications

urlpatterns = [
    path('', NotificationsIndex.as_view(), name='notification-index'),
    path('reset', reset_notifications, name='reset-notifications'),
]
