from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

class Profile(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=300, default="hello, world!") #hammed burger
    profile_picture = models.FileField(default='media/profiles/pfps/default.png', null=True, blank=True, upload_to='media/profiles/pfps/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])
    date_made = models.DateTimeField(default=timezone.now)
    passed_milestones = models.PositiveIntegerField(default=0)
    followers = models.ManyToManyField(User, related_name='followers')
    activity = models.ForeignKey("ProfileActivity", null=True, on_delete=models.CASCADE, related_name="activity")
    using_activity = models.BooleanField(default=False)
    id = models.SlugField(primary_key=True)

class Chat(models.Model):
    members = models.ManyToManyField("profiles.Profile", related_name="members")
    messages = models.ManyToManyField("Message", related_name="messages")
    date_made = models.DateTimeField(default=timezone.now)

class Message(models.Model):
    sender = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="sender")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    message = models.TextField()
    date_sent = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    
class ProfileActivity(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    liked_videos = models.ManyToManyField("videos.Video",  related_name='liked_videos')
    disliked_videos = models.ManyToManyField("videos.Video",  related_name='disliked_videos')
    viewed_videos = models.ManyToManyField("videos.Video",  related_name='viewed_videos')
    followed_profiles = models.ManyToManyField(Profile, related_name='followed_profiles')
    searches = models.TextField()