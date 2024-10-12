from django.contrib import admin
from .models import VideoNotification, BaseNotification, UpdateNotification, CommentNotification, FollowNotification, LikeNotification

# Register your models here.

admin.site.register(VideoNotification)
admin.site.register(BaseNotification)
admin.site.register(UpdateNotification)
admin.site.register(CommentNotification)
admin.site.register(FollowNotification)
admin.site.register(LikeNotification)