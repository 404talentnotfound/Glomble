from django.contrib import admin
from django.urls import path
from .views import VideoNotificationsIndex, VideoNotificationSearch

urlpatterns = [
    path('', VideoNotificationsIndex.as_view(), name='notification-index'),
#    path('search/', VideoNotificationSearch.as_view(), name='video-notification-search'),
]
