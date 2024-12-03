from django.contrib import admin
from django.urls import path
from .views import NotificationsIndex

urlpatterns = [
    path('', NotificationsIndex.as_view(), name='notification-index'),
]
