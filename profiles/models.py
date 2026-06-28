from django.db import models
from django.db.models import Avg
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
import magic
from Glomble.pc_prod import client, AWS_STORAGE_BUCKET_NAME
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

def validate_characters(value):
    if value.count('\n') > 50:
        raise ValidationError("Too many newlines.")

def validate_filesize(value):
    if value.size > 10000000:
        raise ValidationError("File is too big (10mb maximum).")
    if value.size < 1024:
        raise ValidationError("File is too small (1kb minimum).")
    
def validate_image(value):
    if magic.Magic(mime=True).from_buffer(value.read(1024)) not in ['image/jpeg', 'image/png']:
        raise ValidationError("File is the wrong format. Allowed formats are png, jpg.")

class ProfileRating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    rated_profile = models.ForeignKey("Profile", on_delete=models.CASCADE, related_name="profile_ratings")
    rating = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    class Meta:
        unique_together = ('rater', 'rated_profile')

class Profile(models.Model): # hi
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, default="hello, world!", validators=[validate_characters]) #hammed burger
    profile_picture = models.FileField(default='profiles/pfps/default.png', blank=True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg']), validate_filesize, validate_image], help_text="(must be a png or jpg between 1kb and 10mb)")
    date_made = models.DateTimeField(default=timezone.now)
    follower_milestones = models.PositiveIntegerField(default=0)
    followers = models.ManyToManyField(User, blank=True, related_name='followers')
    following = models.ManyToManyField("Profile", blank=True, related_name='followed_profiles') # sorry if using the profile model instead of user model is confusing, i want to migrate followers to the profiles field too but i'm terrified of fucking up the db
    id = models.SlugField(primary_key=True)
    notifications = models.ManyToManyField("notifications.BaseNotification", blank=True, related_name='notifications')
    watched_videos = models.ManyToManyField("videos.Video", blank=True, related_name='watched_videos')
    chats = models.ManyToManyField("Chat", blank=True, related_name='chats')
    rating = models.FloatField(default=5, validators=[MinValueValidator(0), MaxValueValidator(5)])
    moderator = models.BooleanField(default=False)
    customisation = models.ForeignKey("ProfileCustomisation", on_delete=models.SET_NULL, null=True, blank=True)
    shadowbanned = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    nominated_video = models.ForeignKey("videos.Video", blank=True, null=True, on_delete=models.SET_NULL)
    nominated_profile = models.ForeignKey("Profile", blank=True, null=True, on_delete=models.SET_NULL)
    noms = models.ManyToManyField("Profile", blank=True, related_name="profile_nominations") # don't worry about the name here, i couldn't name it "nominations" because it conflicted with the nominations field on Video
    videos = models.ManyToManyField("videos.Video", blank=True, related_name='videos')
    comments = models.ManyToManyField("videos.Comment", blank=True, related_name='comments')

    def remove_follows(self):
        for i in self.followers.all():
            profile = Profile.objects.all().get(username=i)
            profile.following.remove(self)

        for i in self.following.all():
            i.followers.remove(self.username)

        self.followers.clear()
        self.following.clear()

    def delete_media(self):
        if self.profile_picture.name != "profiles/pfps/default.png":
            client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=self.profile_picture.name)
            self.profile_picture.name = "profiles/pfps/default.png"
            self.save()
        
        if not self.customisation:
            return
        
        if self.customisation.banner_image:
            client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=self.customisation.banner_image.name)

        if self.customisation.video_banner:
            client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=self.customisation.video_banner.name)

        return

    def recalculate_rating(self):
        avg = ProfileRating.objects.filter(rated_profile=self).aggregate(
            Avg("rating")
        )["rating__avg"]
        self.rating = round(avg or 0, 2)
        self.save(update_fields=["rating"])

    def __str__(self):
        return self.id

class ProfileCustomisation(models.Model):
    customised_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    background_color = models.CharField(blank=True, max_length=7, default="#ffffff")
    accent_color = models.CharField(blank=True, max_length=7, default="#000000")
    use_accent = models.BooleanField(default=True)
    text_color = models.CharField(blank=True, max_length=7, default="#000000")
    use_text_shadow = models.BooleanField(default=True)
    text_shadow_color = models.CharField(blank=True, max_length=7, default="#ffffff")
    video_card_text_color = models.CharField(blank=True, max_length=7, default="#000000")
    video_card_text_shadow_color = models.CharField(blank=True, max_length=7, default="#ffffff")
    use_video_card_text_shadow = models.BooleanField(default=True)
    banner_image = models.FileField(blank=True, validators=[validate_filesize, validate_image])
    video_banner = models.FileField(blank=True, validators=[validate_filesize, validate_image])

    def clean(self):
        cleaned_data = super().clean()
        background_text_contrast = self.is_contrast_good(self.background_color, self.text_color) or self.banner_image
        background_accent_contrast = self.is_contrast_good(self.background_color, self.accent_color) or self.banner_image
        text_shadow_contrast = self.is_contrast_good(self.text_color, self.text_shadow_color)
        video_card_text_shadow_contrast = self.is_contrast_good(self.video_card_text_color, self.video_card_text_shadow_color)

        errors = []
        if not background_accent_contrast and self.use_accent:
            errors.append("Accent color must contrast with the background colour.")
        if not background_text_contrast and (not text_shadow_contrast and self.use_text_shadow) or not self.use_text_shadow:
            errors.append("Text color must contrast with the background.")
        if not video_card_text_shadow_contrast and self.use_video_card_text_shadow:
            errors.append("Video card text shadow must contrast with the video card text color.")

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

        return contrast_ratio >= 1.35
    
class Ban(models.Model):
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    ban_giver = models.ForeignKey("profiles.Profile", null=True, on_delete=models.SET_NULL, related_name="ban_giver") # i can't think of a better word sorry
    given_reason = models.TextField(max_length=1000, help_text="(this will be displayed to the user)")
    description = models.TextField(max_length=1000, blank=True, help_text="(this will only show for you and other admins)")
    delete_all_creations = models.BooleanField(default=True, help_text="This permanently deletes everything but their account (videos, comments, given ratings, etc.)")
    appeals = models.ManyToManyField("BanAppeal", blank=True, related_name='appeals')
    date_made = models.DateTimeField(default=timezone.now)

class BanAppeal(models.Model):
    ban = models.ForeignKey(Ban, on_delete=models.CASCADE)
    appeal_message = models.TextField(max_length=5000)
    number = models.IntegerField(default=0)
    rejected = models.BooleanField(default=False)
    date_made = models.DateTimeField(default=timezone.now)

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