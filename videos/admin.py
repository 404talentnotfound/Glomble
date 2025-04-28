from django.contrib import admin
from .models import Video, Comment

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'uploader', 'unlisted')
    search_fields = ['id', 'title']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'commenter', 'comment')
    search_fields = ['pk']