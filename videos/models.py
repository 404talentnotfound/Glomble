from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from notifications.models import VideoNotification, CommentNotification
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import os
from django.core.exceptions import ValidationError

def validate_characters(value):
    for char in value:
        if len(char.encode('utf-8')) > 3:
            raise ValidationError("Input contains oversized characters.")

class Video(models.Model, object):
    uploader = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, default=1)
    notification_message = models.CharField(max_length=50, default="new video", null=True, validators=[validate_characters])
    title = models.CharField(max_length=75, validators=[validate_characters])
    description = models.CharField(max_length=500, null=True, blank=True, validators=[validate_characters])
    video_file = models.FileField(upload_to='media/uploads/video_files/', validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov'])])
    thumbnail = models.FileField(upload_to='media/uploads/thumbnails/', blank=True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])
    date_posted = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, blank=True, related_name='video_likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='video_dislikes')
    views = models.ManyToManyField(User, blank=True, related_name='video_views')
    duration = models.FloatField(null=True, blank=True)
    unlisted = models.BooleanField(default=False)
    id = models.SlugField(primary_key=True)
    recommendations = models.PositiveIntegerField(default=0)
    comments = models.ManyToManyField("Comment", blank=True, related_name='video_comments')
    push_notification = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
@receiver(post_save, sender=Video)
def video_notify(sender, instance, created, **kwargs):
    if created and instance.push_notification:
        VideoNotification.objects.create(video=instance, message=instance.notification_message)

@receiver(post_delete, sender=Video)
def delete_files(sender, instance, using, **kwargs):
    try:
        os.remove(instance.video_file.name)
        os.remove(instance.thumbnail.name)
    except:
        try:
            os.remove(instance.thumbnail.name)
        except:
            pass

class Comment(models.Model):
    comment = models.CharField(max_length=500, validators=[validate_characters])
    date_posted = models.DateTimeField(default=timezone.now)
    commenter = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, default=1)
    post = models.ForeignKey('Video', on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, blank=True, related_name='comment_likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='comment_dislikes')
    replying_to = models.ForeignKey("Comment", on_delete=models.CASCADE, null=True, blank=True, related_name="reply_to")
    replies = models.ManyToManyField("Comment", blank=True, related_name="comment_replies")

    class Meta:
        ordering = ['-date_posted']

@receiver(post_save, sender=Comment)
def comment_notify(sender, instance, created, **kwargs):
    if created:
        if instance.commenter != instance.post.uploader and instance.replying_to == None:
            CommentNotification.objects.create(comment=instance, message=f'just commented on your video: "{instance.comment}"')
        elif instance.replying_to != None and instance.replying_to.commenter != instance.commenter:
            CommentNotification.objects.create(comment=instance, message=f'just replied to your comment: "{instance.comment}"')