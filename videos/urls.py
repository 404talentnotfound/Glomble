from django.urls import path
from .views import CreateVideo, DetailVideo, UpdateVideo, DeleteVideo, AddLike, Dislike, DownloadVideo, VideoSearch, Recommend, update_video_view_count, update_video_recommendation_count, update_video_like_count, update_comments_like_count, redirect_video
urlpatterns = [
    path('create/', CreateVideo.as_view(), name='video-create'),
    path('search/', VideoSearch.as_view(), name='video-search'),
    path('<slug:id>/', redirect_video),
    path('<slug:id>', DetailVideo.as_view(), name='video-detail'),
    path('<slug:id>/update', UpdateVideo.as_view(), name='video-update'),
    path('<slug:id>/delete', DeleteVideo.as_view(), name='video-delete'),
    path('<slug:id>/like', AddLike.as_view(), name='video-like'),
    path('<slug:id>/dislike', Dislike.as_view(), name='video-dislike'),
    path('<slug:id>/download', DownloadVideo.as_view(), name='video-download'),
    path('<slug:id>/recommend', Recommend.as_view(), name='video-recommend'),
    path('<slug:id>/update-view-count/', update_video_view_count),
    path('<slug:id>/update-recommendation-count/', update_video_recommendation_count),
    path('<slug:id>/update-likes-count/', update_video_like_count),
    path('<slug:id>/update-comment-likes-count/', update_comments_like_count),
]
