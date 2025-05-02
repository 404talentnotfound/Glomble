from django.db import models
from django.contrib import admin
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
import magic

def validate_characters(value):
    if value.count('\n') > 10:
        raise ValidationError("Too many newlines.")

def validate_filesize(value):
    if not 1024 < value.size < 10000000:
        raise ValidationError("File is too big or too small.")
    
def validate_image(value):
    if magic.Magic(mime=True).from_buffer(value.read(1024)) not in ['image/jpeg', 'image/png']:
        raise ValidationError("File is the wrong format. Allowed formats are png, jpg.")

class ProfileRating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    rated_profile = models.ForeignKey("Profile", on_delete=models.CASCADE, related_name="profile_ratings")
    rating = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    class Meta:
        unique_together = ('rater', 'rated_profile')

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
    ratings = models.JSONField(default=dict, blank=True, null=True)
    rating = models.FloatField(default=5, validators=[MinValueValidator(0), MaxValueValidator(5)])
    moderator = models.BooleanField(default=False)
    helper = models.BooleanField(default=False)
    customisation = models.ForeignKey("ProfileCustomisation", on_delete=models.SET_NULL, null=True, blank=True)
    shadowbanned = models.BooleanField(default=False)
    videos = models.ManyToManyField("videos.Video", blank=True, related_name='videos')

    def update_rating(self):
        ratings = self.profile_ratings.all().values_list('rating', flat=True)
        self.rating = sum(ratings) / len(ratings) if ratings else 5
        self.save()

    def __str__(self):
        return self.id
    
class ProfileCustomisation(models.Model):
    customised_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    background_color = models.CharField(blank=True, max_length=7, default="#ffffff")
    text_color = models.CharField(blank=True, max_length=7, default="#000000")
    text_shadow_color = models.CharField(blank=True, max_length=7, default="#ffffff")
    video_card_text_color = models.CharField(blank=True, max_length=7, default="#000000")
    video_card_text_shadow_color = models.CharField(blank=True, max_length=7, default="#ffffff")
    banner_image = models.FileField(blank=True, upload_to='profiles/banners/', validators=[validate_filesize, validate_image])
    video_banner = models.FileField(blank=True, upload_to='profiles/video_banners/', validators=[validate_filesize, validate_image])

    def clean(self):
        cleaned_data = super().clean()

        background_text_contrast = self.is_contrast_good(self.background_color, self.text_color)
        background_shadow_contrast = self.is_contrast_good(self.background_color, self.text_shadow_color)
        text_shadow_contrast = self.is_contrast_good(self.text_color, self.text_shadow_color)
        video_card_text_shadow_contrast = self.is_contrast_good(self.video_card_text_color, self.video_card_text_shadow_color)

        errors = []
        if not (background_text_contrast or background_shadow_contrast):
            errors.append("Text color must contrast with the background.")
        if not text_shadow_contrast:
            errors.append("Text shadow must contrast with the text color.")
        if not video_card_text_shadow_contrast:
            errors.append("Video card text shadow must contrast with the text color.")

        if errors:
            raise ValidationError(errors)

        return cleaned_data

    def is_contrast_good(self, color1, color2):
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) != 6:
                return (0, 0, 0)
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def relative_luminance(r, g, b):
            def srgb(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

            r, g, b = srgb(r), srgb(g), srgb(b)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)

        lum1 = relative_luminance(*rgb1)
        lum2 = relative_luminance(*rgb2)

        L1, L2 = max(lum1, lum2), min(lum1, lum2)
        contrast_ratio = (L1 + 0.05) / (L2 + 0.05)

        return contrast_ratio >= 2.5

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
