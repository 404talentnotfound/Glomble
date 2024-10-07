from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from profiles.models import Profile
from django.db.models.signals import post_save
from django.dispatch import receiver

class VideoNotification(models.Model, object):
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE)
    notified_profiles = models.ManyToManyField(Profile, blank=True, related_name='notified_profiles', through="BaseNotification")
    message = models.CharField(max_length=200, null=True, default="greg bog")
    date_made = models.DateTimeField(default=timezone.now)

class UpdateNotification(models.Model, object):
    message = models.CharField(max_length=200, null=True, default="added peanut butter sandwiches")
    date_made = models.DateTimeField(default=timezone.now)

class BaseNotification(models.Model, object):
    notification = models.ForeignKey(VideoNotification, on_delete=models.CASCADE)
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    date_notified = models.DateTimeField(default=timezone.now)

@receiver(post_save, sender=VideoNotification)
def notify(sender, instance, created, **kwargs):
    if created:
        for follower in instance.video.uploader.followers.all():
            BaseNotification.objects.create(notification=instance, profile=Profile.objects.all().get(username=follower))
