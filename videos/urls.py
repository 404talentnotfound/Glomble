from django.urls import path
from .views import CreateVideo, DetailVideo, UpdateVideo, DeleteVideo, AddLike, Dislike, DownloadVideo, Recommend, update_video_view_count, redirect_video, get_recommended_videos
urlpatterns = [
    path('create/', CreateVideo.as_view(), name='video-create'),
    path('get-recommendations/<str:category>', get_recommended_videos),
    path('<slug:id>/', redirect_video),
    path('<slug:id>', DetailVideo.as_view(), name='video-detail'),
    path('<slug:id>/update', UpdateVideo.as_view(), name='video-update'),
    path('<slug:id>/delete', DeleteVideo.as_view(), name='video-delete'),
    path('<slug:id>/like', AddLike.as_view(), name='video-like'),
    path('<slug:id>/dislike', Dislike.as_view(), name='video-dislike'),
    path('<slug:id>/download', DownloadVideo.as_view(), name='video-download'),
    path('<slug:id>/recommend', Recommend.as_view(), name='video-recommend'),
    path('<slug:id>/update-view-count/', update_video_view_count),
]
