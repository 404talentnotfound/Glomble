from django.urls import path
from .views import DeleteComment, AddLike, Dislike, UpdateComment, PinComment

app_name='comments'

urlpatterns = [
    path('<int:pk>/pin', PinComment.as_view(), name='comment-pin'),
    path('<int:pk>/delete', DeleteComment.as_view(), name='comment-delete'),
    path('<int:pk>/edit', UpdateComment.as_view(), name='comment-update'),
    path('<int:pk>/like', AddLike.as_view(), name='comment-like'),
    path('<int:pk>/dislike', Dislike.as_view(), name='comment-dislike'),
]