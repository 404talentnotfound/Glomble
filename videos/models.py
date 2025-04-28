from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from notifications.models import VideoNotification, CommentNotification
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import os
from django.core.exceptions import ValidationError

# does more than just validate the length but renaming a validator function messes migrations up
def validate_length(value: str):
    if len(value) > 500:
        raise ValidationError("Input is too long.")
    if value.count('\n') > 10:
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
    description = models.TextField(null=True, blank=True, validators=[validate_length], help_text="(must be under 500 characters)")
    video_file = models.FileField(upload_to='media/uploads/video_files/', validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov'])], help_text="(must be an mp4 or mov between 1kb and 5gb and be under 2 hours)")
    thumbnail = models.FileField(upload_to='media/uploads/thumbnails/', blank=True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'gif'])], help_text="(must be a png or jpg between 1kb and 10mb)")
    date_posted = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, blank=True, related_name='video_likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='video_dislikes')
    views = models.ManyToManyField(User, blank=True, related_name='video_views')
    duration = models.FloatField(null=True, blank=True)
    unlisted = models.BooleanField(default=False)
    id = models.SlugField(primary_key=True)
    recommendations = models.PositiveIntegerField(default=0)
    comments = models.ManyToManyField("Comment", blank=True, related_name='video_comments')
    pinned_comment = models.ForeignKey("Comment", null=True, blank=True, on_delete=models.CASCADE)
    push_notification = models.BooleanField(default=True)
    recommendation_milestones = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=13,
                  choices=CATAGORIES,
                  default=ENTERTAINMENT)

    def __str__(self):
        return self.id
    
@receiver(post_save, sender=Video)
def video_created(sender, instance, created, **kwargs):
    if created:
        instance.uploader.videos.add(instance)
        if instance.push_notification:
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
    comment = models.TextField(validators=[validate_length])
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