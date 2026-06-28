from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from notifications.models import VideoNotification, CommentNotification
from django.db.models.signals import post_delete, post_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from Glomble.pc_prod import client, AWS_STORAGE_BUCKET_NAME

def validate_characters(value: str):
    if value.count('\n') > 50:
        raise ValidationError("Too many newlines.")

ART = "Art"
ANIMATION = "Animation"
DISCUSSION = "Discussion"
EDUCATION = "Education"
ENTERTAINMENT = "Entertainment"
GAMING = "Gaming"
MEMES = "Memes"
MUSIC = "Music"
MISCELLANEOUS = "Miscellaneous"

# how did i only just now notice i misspelled categories
CATAGORIES = (
    (ART, "Art"),
    (ANIMATION, "Animation"),
    (DISCUSSION, "Discussion"),
    (EDUCATION, "Education"),
    (ENTERTAINMENT, "Entertainment"),
    (GAMING, "Gaming"),
    (MEMES, "Memes"),
    (MUSIC, "Music"),
    (MISCELLANEOUS, "Miscellaneous"),
)

class Video(models.Model):
    uploader = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, default=1)
    notification_message = models.CharField(max_length=50, default="new video", blank=True)
    title = models.CharField(max_length=75)
    description = models.TextField(blank=True, null=True, validators=[validate_characters], help_text="(must be under 1000 characters)", max_length=1000)
    video_file = models.FileField(validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov'])], help_text="(must be an mp4 or mov between 1kb and 100mb and be under 2 hours)")
    thumbnail = models.FileField(blank=True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'gif'])], help_text="(must be a png or jpg between 1kb and 5mb)")
    date_posted = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, blank=True, related_name='video_likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='video_dislikes')
    views = models.ManyToManyField(User, blank=True, related_name='video_views')
    duration = models.FloatField(null=True, blank=True)
    unlisted = models.BooleanField(default=False)
    id = models.SlugField(primary_key=True)
    recommendations = models.ManyToManyField("profiles.Profile", blank=True, related_name='video_recommendations')
    score = models.FloatField(default=0)
    comments = models.ManyToManyField("Comment", blank=True, related_name='video_comments')
    pinned_comment = models.ForeignKey("Comment", null=True, blank=True, on_delete=models.SET_NULL)
    push_notification = models.BooleanField(default=True)
    recommendation_milestones = models.PositiveIntegerField(default=0)
    nominations = models.ManyToManyField("profiles.Profile", blank=True, related_name="nominations")
    category = models.CharField(max_length=13,
                  choices=CATAGORIES,
                  default=ENTERTAINMENT)

def calculate_score(video):
    like_count = video.likes.count()
    dislike_count = video.dislikes.count()
    total_votes = like_count + dislike_count
    likeratio = like_count / total_votes if total_votes > 0 else 1

    # I realise this formula is long as fuck but it's quite simple (could prob be shortened though)
    # it takes the amount of user given recommendations,
    # multiplies it by the uploader's rating,
    # multiplies that by the like-dislike ratio (decimal number between 0-1, 1 meaning it has no dislikes)
    # and finally multiplies that by the video duration in seconds divided by 180 to encourage longer videos (decimal number between 0-1, 1 being for 3 minutes or above)
    new_score = round(video.recommendations.count() * video.uploader.rating * likeratio * round(min(video.duration, 180)/180, 2), 1)

    if new_score < video.recommendations.count():
        new_score = video.recommendations.count()
            
    video.score = new_score

def batch_calculate_score(video_queryset):
    videos = video_queryset.select_related('uploader').prefetch_related('likes', 'dislikes')

    for video in videos:
        calculate_score(video)

    Video.objects.bulk_update(videos, ['score'])

@receiver(m2m_changed, sender=Video.recommendations.through)
def on_recommendation_change(sender, instance: Video, action, **kwargs):
    calculate_score(instance)

@receiver(post_save, sender=Video)
def video_created(sender, instance, created, **kwargs):
    if created:
        instance.uploader.videos.add(instance)
        if instance.push_notification and not (instance.uploader.shadowbanned):
            VideoNotification.objects.create(video=instance, message=instance.notification_message)

@receiver(post_delete, sender=Video)
def delete_files(sender, instance, using, **kwargs):
    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=instance.video_file.name)
    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=instance.thumbnail.name)

class Comment(models.Model):
    comment = models.TextField(validators=[validate_characters], max_length=1000)
    date_posted = models.DateTimeField(default=timezone.now)
    commenter = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, default=1)
    post = models.ForeignKey('Video', on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, blank=True, related_name='comment_likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='comment_dislikes')
    replying_to = models.ForeignKey("Comment", on_delete=models.CASCADE, null=True, blank=True, related_name="reply_to")
    replies = models.ManyToManyField("Comment", blank=True, related_name="comment_replies")

@receiver(post_save, sender=Comment)
def comment_notify(sender, instance, created, **kwargs):
    if created and not (instance.commenter.shadowbanned):
        CommentNotification.objects.create(comment=instance, message=f'just commented: "{instance.comment}"')