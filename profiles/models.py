from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User

class Profile(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=300, default="hello, world!") #hammed burger
    profile_picture = models.FileField(default='media/profiles/pfps/default.png', null=True, blank=True, upload_to='media/profiles/pfps/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])
    date_made = models.DateTimeField(default=timezone.now)
    followers = models.ManyToManyField(User, blank=True, related_name='followers')
    id = models.SlugField(primary_key=True)
