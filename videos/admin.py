from django.contrib import admin
from .models import Video, Comment

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'uploader', 'uploader__username', 'unlisted')
    search_fields = ['id', 'title', 'uploader__username__username']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'commenter', 'commenter__username', 'comment')
    search_fields = ['id', 'commenter__username__username']