from django.contrib import admin
from django.urls import path
from .views import NotificationsIndex, VideoNotificationSearch

urlpatterns = [
    path('', NotificationsIndex.as_view(), name='notification-index'),
#    path('search/', VideoNotificationSearch.as_view(), name='video-notification-search'),
]
