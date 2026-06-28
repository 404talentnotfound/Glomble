from django.contrib import admin
from django.urls import path
from . import views as views
urlpatterns = [
    path('', views.ProfileIndex.as_view(), name='profile-index'),
    path('chats', views.ChatIndex.as_view(), name='chat-index'),
    path('unban/<int:id>', views.RemoveBan.as_view(), name='remove-ban'),
    path('<slug:id>/', views.redirect_profile),
    path('<slug:id>/customise', views.customise_profile, name='customise-profile'),
    path('<slug:id>/rate', views.rate_profile, name='rate-profile'),
    path('<slug:id>/chats', views.DetailChat.as_view(), name='chat-detail'),
    path('<slug:id>/', views.redirect_profile),
    path('<slug:id>', views.DetailProfileIndex.as_view(), name='detail-profile'),
    path('<slug:id>/update', views.UpdateProfile.as_view(), name='profile-update'),
    path('<slug:id>/delete', views.DeleteProfile.as_view(), name='profile-delete'),
    path('<slug:id>/followers/add', views.AddFollower.as_view(), name='add-follower'),
    path('<slug:id>/followers/remove', views.RemoveFollower.as_view(), name='remove-follower'),
    path('<slug:id>/nominate', views.Nominate.as_view(), name='profile-nominate'),
    path('<slug:id>/ban', views.CreateBan.as_view(), name='create-ban'),
    path('<slug:id>/shadowban', views.ShadowBan.as_view(), name='shadowban'),
    path('<slug:id>/appeal/<int:num>', views.DetailBanAppeal.as_view(), name='detail-appeal'),
    path('<slug:id>/appeal/<int:num>/remove', views.RejectBanAppeal.as_view(), name='reject-ban-appeal'),
    path('<slug:id>/update-follow-count/', views.update_profile_follow_count),
]