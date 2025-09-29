from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from notifications.models import VideoNotification, CommentNotification
from django.db.models.signals import post_delete, post_save, m2m_changed
from django.dispatch import receiver
import os
from django.core.exceptions import ValidationError
from Glomble.pc_prod import client, AWS_STORAGE_BUCKET_NAME

def validate_characters(value: str):
    if len(value) > 500:
        raise ValidationError("Input is too long.")
    if value.count('\n') > 20:
        raise ValidationError("Too many newlines.")
        
MEMES = "Memes"
GAMING = "Gaming"
EDUCATION = "Education"
ANIMATION = "Animation"
ENTERTAINMENT = "Entertainment"
MUSIC = "Music"
DISCUSSION = "Discussion"
MISCELLANEOUS = "Miscellaneous"
        
CATAGORIES = (
    (MEMES, "Memes"),
    (GAMING, "Gaming"),
    (EDUCATION, "Education"),
    (ANIMATION, "Animation"),
    (ENTERTAINMENT, "Entertainment"),
    (MUSIC, "Music"),
    (DISCUSSION, "Discussion"),
    (MISCELLANEOUS, "Miscellaneous"),
)

class Video(models.Model, object):
    uploader = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, default=1)
    notification_message = models.CharField(max_length=50, default="new video", null=True)
    title = models.CharField(max_length=75)
    description = models.TextField(null=True, blank=True, validators=[validate_characters], help_text="(must be under 500 characters)")
    video_file = models.FileField(validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov'])], help_text="(must be an mp4 or mov between 1kb and 100mb and be under 2 hours)")
    thumbnail = models.FileField(blank=True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'gif'])], help_text="(must be a png or jpg between 1kb and 10mb)")
    date_posted = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, blank=True, related_name='video_likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='video_dislikes')
    views = models.ManyToManyField(User, blank=True, related_name='video_views')
    duration = models.FloatField(null=True, blank=True)
    unlisted = models.BooleanField(default=False)
    id = models.SlugField(primary_key=True)
    recommendations = models.ManyToManyField("profiles.Profile", blank=True, related_name='video_recommendations')
    score = models.FloatField(default=0)
    comments = models.ManyToManyField("Comment", blank=True, related_name='video_comments')
    pinned_comment = models.ForeignKey("Comment", null=True, blank=True, on_delete=models.SET_NULL)
    push_notification = models.BooleanField(default=True)
    recommendation_milestones = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=13,
                  choices=CATAGORIES,
                  default=ENTERTAINMENT)

@receiver(m2m_changed, sender=Video.recommendations.through)
def on_recommendation_change(sender, instance: Video, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        days = (timezone.now() - instance.date_posted).days
        like_count = instance.likes.count()
        dislike_count = instance.dislikes.count()
        total_votes = like_count + dislike_count

        likeratio = like_count / total_votes if total_votes > 0 else 1
        if likeratio == 0:
            likeratio = .1

        if instance.duration > 180 and instance.category != "Meme":
            instance.score = round((instance.recommendations.count() * instance.uploader.rating) * likeratio, 1)
        else:
            instance.score = instance.recommendations.count()

        instance.save(update_fields=["score"])

@receiver(post_save, sender=Video)
def video_created(sender, instance, created, **kwargs):
    if created:
        instance.uploader.videos.add(instance)
        if instance.push_notification:
            VideoNotification.objects.create(video=instance, message=instance.notification_message)

@receiver(post_delete, sender=Video)
def delete_files(sender, instance, using, **kwargs):
    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"{instance.video_file.name}")
    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"{instance.thumbnail.name}")

class Comment(models.Model):
    comment = models.TextField(validators=[validate_characters])
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
        elif instance.replying_to != None:
            CommentNotification.objects.create(comment=instance, message=f'just replied to your comment: "{instance.comment}"')
