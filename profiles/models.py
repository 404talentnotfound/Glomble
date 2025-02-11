from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

def validate_characters(value):
    for char in value:
        if len(char.encode('utf-8')) > 3:
            raise ValidationError("Input contains oversized characters.")

class Profile(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, default="hello, world!", validators=[validate_characters]) #hammed burger
    profile_picture = models.FileField(default='profiles/pfps/default.png', blank=True, upload_to='media/profiles/pfps/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])], help_text="(must be a png or jpg between 1kb and 10mb)")
    date_made = models.DateTimeField(default=timezone.now)
    follower_milestones = models.PositiveIntegerField(default=0)
    followers = models.ManyToManyField(User, related_name='followers')
    id = models.SlugField(primary_key=True)
    notifications = models.ManyToManyField("notifications.BaseNotification", blank=True, related_name='notifications')
    watched_videos = models.ManyToManyField("videos.Video", blank=True, related_name='watched_videos')
    chats = models.ManyToManyField("Chat", blank=True, related_name='chats')
    recommendations_left = models.PositiveIntegerField(default=3)
    ratings = models.JSONField(default=dict, blank=True, null=True)
    rating = models.FloatField(default=5, validators=[MinValueValidator(0), MaxValueValidator(5)])
    moderator = models.BooleanField(default=False)
    helper = models.BooleanField(default=False)
    customisation = models.ForeignKey("ProfileCustomisation", on_delete=models.SET_NULL, null=True, blank=True)
    shadowbanned = models.BooleanField(default=False)

    def update_rating(self):
        if self.ratings:
            self.rating = sum(self.ratings.values()) / len(self.ratings)
        else:
            self.rating = 5
        self.save()

    def __str__(self):
        return self.id
    
class ProfileCustomisation(models.Model):
    customised_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    background_color = models.CharField(max_length=7, default="#ffffff", help_text="Background color in hex.")
    text_color = models.CharField(max_length=7, default="#000000", help_text="Text color in hex.")
    text_shadow_color = models.CharField(max_length=7, default="#ffffff", help_text="Text shadow color in hex.")
    banner_image = models.FileField(blank=True, upload_to='profiles/banners/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])], help_text="(must be a png or jpg between 1kb and 10mb)")
    video_banner = models.FileField(blank=True, upload_to='profiles/video_banners/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])], help_text="(must be a png or jpg between 1kb and 10mb)")

    def __str__(self):
        return f"{self.customised_profile.id}'s customised profile"

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
