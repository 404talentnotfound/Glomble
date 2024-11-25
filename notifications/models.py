from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from profiles.models import Profile
from django.db.models.signals import post_save
from django.dispatch import receiver

class VideoNotification(models.Model, object):
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE)
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=50, null=True, default="greg bog")
    date_made = models.DateTimeField(default=timezone.now)

class CommentNotification(models.Model, object):
    comment = models.ForeignKey('videos.Comment', on_delete=models.CASCADE)
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=50, null=True, default="Someone just commented on your video")
    date_made = models.DateTimeField(default=timezone.now)

class UpdateNotification(models.Model, object):
    message = models.CharField(max_length=200, null=True, default="added peanut butter sandwiches")
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    date_made = models.DateTimeField(default=timezone.now)

class FollowNotification(models.Model, object):
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name="milestone_profile")
    message = models.CharField(max_length=75, null=True, default="You reached a new follower milestone!")
    follower = models.ForeignKey('profiles.Profile', null=True, on_delete=models.CASCADE, related_name="follower")
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    date_made = models.DateTimeField(default=timezone.now)

class BaseNotification(models.Model, object):
    video_notification = models.ForeignKey(VideoNotification, on_delete=models.CASCADE, null=True, blank=True)
    comment_notification = models.ForeignKey(CommentNotification, on_delete=models.CASCADE, null=True, blank=True)
    update_notification = models.ForeignKey(UpdateNotification, on_delete=models.CASCADE, null=True, blank=True)
    follow_notification = models.ForeignKey(FollowNotification, on_delete=models.CASCADE, null=True, blank=True)
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    date_notified = models.DateTimeField(default=timezone.now)

@receiver(post_save, sender=VideoNotification)
def video_notify(sender, instance, created, **kwargs):
    if created:
        for follower in instance.video.uploader.followers.all():
            BaseNotification.objects.create(video_notification=instance, profile=Profile.objects.all().get(username=follower))

@receiver(post_save, sender=CommentNotification)
def comment_notify(sender, instance, created, **kwargs):
    if created:
        if instance.comment.replying_to == None:
            BaseNotification.objects.create(comment_notification=instance, profile=instance.comment.post.uploader)
        else:
            BaseNotification.objects.create(comment_notification=instance, profile=instance.comment.replying_to.commenter)

@receiver(post_save, sender=UpdateNotification)
def update_notify(sender, instance, created, **kwargs):
    if created:
        for profile in Profile.objects.all():
            BaseNotification.objects.create(update_notification=instance, profile=profile)

@receiver(post_save, sender=FollowNotification)
def follow_notify(sender, instance, created, **kwargs):
    if created:
        BaseNotification.objects.create(follow_notification=instance, profile=instance.profile)

@receiver(post_save, sender=BaseNotification)
def add_notification_to_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.all().get(id=instance.profile.id).notifications.add(instance)