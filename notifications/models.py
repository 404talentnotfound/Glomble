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

class MilestoneNotification(models.Model, object):
    profile = models.ForeignKey('profiles.Profile', blank=True, null=True, on_delete=models.CASCADE, related_name="milestone_profile")
    video = models.ForeignKey('videos.Video', blank=True, null=True, on_delete=models.CASCADE, related_name="milestone_video")
    message = models.CharField(max_length=75, null=True, default="You reached a new follower milestone!")
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    date_made = models.DateTimeField(default=timezone.now)

class BaseNotification(models.Model, object):
    video_notification = models.ForeignKey(VideoNotification, on_delete=models.CASCADE, null=True, blank=True)
    comment_notification = models.ForeignKey(CommentNotification, on_delete=models.CASCADE, null=True, blank=True)
    update_notification = models.ForeignKey(UpdateNotification, on_delete=models.CASCADE, null=True, blank=True)
    milestone_notification = models.ForeignKey(MilestoneNotification, on_delete=models.CASCADE, null=True, blank=True)
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    date_notified = models.DateTimeField(default=timezone.now)

@receiver(post_save, sender=VideoNotification)
def video_notify(sender, instance, created, **kwargs):
    if created:
        followers = instance.video.uploader.followers.all()
        profiles = Profile.objects.filter(username__in=followers)

        notifications = [BaseNotification(video_notification=instance, profile=profile) for profile in profiles]

        BaseNotification.objects.bulk_create(notifications)

        created_notifications = BaseNotification.objects.all().filter(
            video_notification=instance,
        )

        through_model = Profile.notifications.through
        through_model.objects.bulk_create([
            through_model(
                profile_id=notification.profile_id,
                basenotification_id=notification.id
            )
            for notification in created_notifications
        ])

@receiver(post_save, sender=CommentNotification)
def comment_notify(sender, instance, created, **kwargs):
    if created:
        if instance.comment.replying_to == None:
            BaseNotification.objects.create(comment_notification=instance, profile=instance.comment.post.uploader)
        else:
            if instance.comment.replying_to.commenter != instance.comment.commenter:
                BaseNotification.objects.create(comment_notification=instance, profile=instance.comment.replying_to.commenter)

            if instance.comment.comment.count(" ") > 0:
                if instance.comment.comment.startswith("@") and Profile.objects.all().filter(username__username=instance.comment.comment.split(" ")[0][1:]).exists():
                    if instance.comment.replying_to.commenter != Profile.objects.all().get(username__username=instance.comment.comment.split(" ")[0][1:]) != instance.comment.commenter:
                        BaseNotification.objects.create(comment_notification=instance, profile=Profile.objects.all().get(username__username=instance.comment.comment.split(" ")[0][1:]))


@receiver(post_save, sender=UpdateNotification)
def update_notify(sender, instance, created, **kwargs):
    if created:
        profiles = Profile.objects.all()

        notifications = [BaseNotification(update_notification=instance, profile=profile) for profile in profiles]
        BaseNotification.objects.bulk_create(notifications)

        created_notifications = BaseNotification.objects.all().filter(
            update_notification=instance,
        )

        through_model = Profile.notifications.through
        through_model.objects.bulk_create([
            through_model(
                profile_id=notification.profile_id,
                basenotification_id=notification.id
            )
            for notification in created_notifications
        ])

@receiver(post_save, sender=MilestoneNotification)
def milestone_notify(sender, instance, created, **kwargs):
    if created:
        if instance.profile != None:
            BaseNotification.objects.create(milestone_notification=instance, profile=instance.profile)
        elif instance.video != None:
            BaseNotification.objects.create(milestone_notification=instance, profile=instance.video.uploader)

@receiver(post_save, sender=BaseNotification)
def add_notification_to_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.all().get(id=instance.profile.id).notifications.add(instance)
        if Profile.objects.all().get(id=instance.profile.id).notifications.count() > 50:
            Profile.objects.all().get(id=instance.profile.id).notifications.remove(Profile.objects.all().get(id=instance.profile.id).notifications.first())
