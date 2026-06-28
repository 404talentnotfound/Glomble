from django.db import models
from django.utils import timezone
from profiles.models import Profile
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
import re

class VideoNotification(models.Model, object):
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE)
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=75, null=True, default="greg bog")
    date_made = models.DateTimeField(default=timezone.now)

class CommentNotification(models.Model, object):
    comment = models.ForeignKey('videos.Comment', on_delete=models.CASCADE)
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=50, null=True, default="Someone just commented on your video")
    date_made = models.DateTimeField(default=timezone.now)

class UpdateNotification(models.Model, object):
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=200, null=True, default="added peanut butter sandwiches")
    date_made = models.DateTimeField(default=timezone.now)

class MilestoneNotification(models.Model, object):
    profile = models.ForeignKey('profiles.Profile', blank=True, null=True, on_delete=models.CASCADE, related_name="milestone_profile")
    video = models.ForeignKey('videos.Video', blank=True, null=True, on_delete=models.CASCADE, related_name="milestone_video")
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=75, null=True, default="You reached a new follower milestone!")
    date_made = models.DateTimeField(default=timezone.now)

class MiscellaneousNotification(models.Model, object):
    notified_profiles = models.ManyToManyField(Profile, blank=True, through="BaseNotification")
    message = models.CharField(max_length=75, null=True, blank=True, default="hi i'm a placeholder nice to meet you")
    comment = models.ForeignKey('videos.Comment', null=True, blank=True, on_delete=models.CASCADE, related_name="linked_comment")
    video = models.ForeignKey('videos.Video', null=True, blank=True, on_delete=models.CASCADE, related_name="linked_video")
    profile = models.ForeignKey('profiles.Profile', null=True, blank=True, on_delete=models.CASCADE, related_name="linked_profile")
    date_made = models.DateTimeField(default=timezone.now)

class BaseNotification(models.Model, object):
    video_notification = models.ForeignKey(VideoNotification, on_delete=models.CASCADE, null=True, blank=True)
    comment_notification = models.ForeignKey(CommentNotification, on_delete=models.CASCADE, null=True, blank=True)
    update_notification = models.ForeignKey(UpdateNotification, on_delete=models.CASCADE, null=True, blank=True)
    milestone_notification = models.ForeignKey(MilestoneNotification, on_delete=models.CASCADE, null=True, blank=True)
    miscellaneous_notification = models.ForeignKey(MiscellaneousNotification, on_delete=models.CASCADE, null=True, blank=True)
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    priority_level = models.IntegerField(default=0)
    requires_action = models.BooleanField(default=False) # This isn't finished but it will be useful in the future, any code i write today is code i wont't have to write tomorrow :)
    date_notified = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['priority_level']

@receiver(post_save, sender=VideoNotification)
def video_notify(sender, instance, created, **kwargs):
    if created:
        followers = instance.video.uploader.followers.all()
        profiles = Profile.objects.filter(username__in=followers)

        notifications = [BaseNotification(video_notification=instance, profile=profile) for profile in profiles]

        BaseNotification.objects.bulk_create(notifications)

@receiver(post_save, sender=CommentNotification)
def comment_notify(sender, instance, created, **kwargs):
    if created:
        if instance.comment.commenter == instance.comment.post.uploader:
            return

        if instance.comment.replying_to == None:
            BaseNotification.objects.create(comment_notification=instance, profile=instance.comment.post.uploader)
            notified_profile = instance.comment.post.uploader
        else:
            if instance.comment.replying_to.commenter != instance.comment.commenter:
                BaseNotification.objects.create(comment_notification=instance, profile=instance.comment.replying_to.commenter)
                notified_profile = instance.comment.replying_to.commenter
            else:
                notified_profile = None

        mentions = re.findall(r'@([^(\n )]+)', instance.comment.comment)

        if mentions:
            mentions = mentions[0]
            if Profile.objects.all().filter(username__username=mentions).exists():
                if notified_profile != Profile.objects.all().get(username__username=mentions):
                    BaseNotification.objects.create(comment_notification=instance, profile=Profile.objects.all().get(username__username=mentions))

@receiver(post_save, sender=UpdateNotification)
def update_notify(sender, instance, created, **kwargs):
    if created:
        profiles = Profile.objects.all()

        notifications = [BaseNotification(update_notification=instance, profile=profile, priority_level=3) for profile in profiles]
        BaseNotification.objects.bulk_create(notifications)

@receiver(post_save, sender=MilestoneNotification)
def milestone_notify(sender, instance, created, **kwargs):
    if created:
        if instance.profile:
            BaseNotification.objects.create(milestone_notification=instance, profile=instance.profile, priority_level=2)
        elif instance.video:
            BaseNotification.objects.create(milestone_notification=instance, profile=instance.video.uploader, priority_level=1)

# Not the ideal way of doing this but it'll work for now
# Also there is no mistake checking, be careful!!
def send_misc_notification(profiles_to_notify, **kwargs):
    if not kwargs["message"]:
        return
    
    misc_notif = MiscellaneousNotification.objects.create()

    # this feels really repetitive, there has to be a quicker way to write this right?
    misc_notif.message = kwargs["message"]
    if "video" in kwargs:
        misc_notif.video = kwargs["video"]
    if "comment" in kwargs:
        misc_notif.comment = kwargs["comment"]
    if "profile" in kwargs:
        misc_notif.profile = kwargs["profile"]
    misc_notif.save()

    priority_level = 0
    requires_action = False

    if "priority_level" in kwargs:
        priority_level = kwargs["priority_level"]
    
    if "requires_action" in kwargs:
        requires_action = kwargs["requires_action"]
    
    BaseNotification.objects.bulk_create([
        BaseNotification(
            miscellaneous_notification=misc_notif,
            profile=profile,
            priority_level=priority_level,
            requires_action=requires_action,
        )
        for profile in profiles_to_notify
    ])
    return