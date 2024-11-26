from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

def validate_characters(value):
    for char in value:
        if len(char.encode('utf-8')) > 1:
            raise ValidationError("Input contains oversized characters.")

class Profile(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, default="hello, world!", validators=[validate_characters]) #hammed burger
    profile_picture = models.FileField(default='media/profiles/pfps/default.png', null=True, blank=True, upload_to='media/profiles/pfps/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])
    date_made = models.DateTimeField(default=timezone.now)
    passed_milestones = models.PositiveIntegerField(default=0)
    followers = models.ManyToManyField(User, related_name='followers')
    id = models.SlugField(primary_key=True)
    notifications = models.ManyToManyField("notifications.BaseNotification", blank=True, related_name='notifications')
    watched_videos = models.ManyToManyField("videos.Video", blank=True, related_name='watched_videos')
    chats = models.ManyToManyField("Chat", blank=True, related_name='chats')
    last_recommend = models.DateTimeField(default=timezone.datetime(1970,1,1,0,1,1))
    rating = models.PositiveIntegerField(default=5)

class Chat(models.Model):
    members = models.ManyToManyField("profiles.Profile", related_name="members")
    messages = models.ManyToManyField("Message", related_name="messages")
    date_made = models.DateTimeField(default=timezone.now)

class Message(models.Model):
    sender = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="sender")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    message = models.TextField(max_length=1000, validators=[validate_characters])
    date_sent = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    