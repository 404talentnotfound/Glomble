from django.contrib import admin
from django.urls import path
from .views import DeleteComment, AddLike, Dislike

app_name='comments'

urlpatterns = [
    path('<int:pk>/delete', DeleteComment.as_view(), name='comment-delete'),
    path('<int:pk>/like', AddLike.as_view(), name='comment-like'),
    path('<int:pk>/dislike', Dislike.as_view(), name='comment-dislike'),

]