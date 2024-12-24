from django.contrib import admin
from django.urls import path
from .views import ProfileIndex, DetailProfileIndex, UpdateProfile, DeleteProfile, AddFollower, RemoveFollower, UserSearch, DetailChat, ChatIndex, create_profile, update_profile_follow_count, redirect_profile, customise_profile, rate_profile, send_email
urlpatterns = [
    path('', ProfileIndex.as_view(), name='profile-index'),
    path('create', create_profile, name='create-profile'),
    path('search/', UserSearch.as_view(), name='profile-search'),
    path('chats', ChatIndex.as_view(), name='chat-index'),
    path('<slug:id>/customise', customise_profile, name='customise-profile'),
    path('<slug:id>/rate', rate_profile, name='rate-profile'),
    path('<slug:id>/chats', DetailChat.as_view(), name='chat-detail'),
    path('<slug:id>/', redirect_profile),
    path('<slug:id>', DetailProfileIndex.as_view(), name='detail-profile'),
    path('<slug:id>/update', UpdateProfile.as_view(), name='profile-update'),
    path('<slug:id>/delete', DeleteProfile.as_view(), name='profile-delete'),
    path('<slug:id>/followers/add', AddFollower.as_view(), name='add-follower'),
    path('<slug:id>/followers/remove', RemoveFollower.as_view(), name='remove-follower'),
    path('<slug:id>/update-follow-count/', update_profile_follow_count),
]