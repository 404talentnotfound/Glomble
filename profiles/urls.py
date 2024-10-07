from django.contrib import admin
from django.urls import path
from .views import ProfileIndex, DetailProfileIndex, UpdateProfile, DeleteProfile, AddFollower, RemoveFollower, UserSearch, create_profile, update_profile_follow_count, redirect_profile

urlpatterns = [
    path('', ProfileIndex.as_view(), name='profile-index'),
    path('create', create_profile, name='create_profile'),
    path('search/', UserSearch.as_view(), name='profile-search'),
    path('<slug:id>/', redirect_profile),
    path('<slug:id>', DetailProfileIndex.as_view(), name='detail-profile'),
    path('<slug:id>/update', UpdateProfile.as_view(), name='profile-update'),
    path('<slug:id>/delete', DeleteProfile.as_view(), name='profile-delete'),
    path('<slug:id>/followers/add', AddFollower.as_view(), name='add-follower'),
    path('<slug:id>/followers/remove', RemoveFollower.as_view(), name='remove-follower'),
    path('<slug:id>/update-follow-count/', update_profile_follow_count),
]