from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class VideoReport(models.Model):
	brief_summary = models.TextField(max_length=50)
	reasoning = models.TextField(max_length=500)
	date_sent = models.DateTimeField(default=timezone.now)
	reporter = models.ForeignKey(User, on_delete=models.CASCADE)
	post = models.ForeignKey('videos.Video', on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		ordering = ['-date_sent']

class ProfileReport(models.Model):
	brief_summary = models.TextField(max_length=50)
	reasoning = models.TextField(max_length=500)
	date_sent = models.DateTimeField(default=timezone.now)
	reporter = models.ForeignKey(User, on_delete=models.CASCADE)
	profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		ordering = ['-date_sent']

class BugReport(models.Model):
	brief_summary = models.TextField(max_length=50)
	explanation = models.TextField(max_length=500)
	date_sent = models.DateTimeField(default=timezone.now)
	reporter = models.ForeignKey(User, on_delete=models.CASCADE)

	class Meta:
		ordering = ['-date_sent']

class Suggestion(models.Model):
	brief_summary = models.TextField(max_length=50)
	explanation = models.TextField(max_length=500)
	date_sent = models.DateTimeField(default=timezone.now)
	reporter = models.ForeignKey(User, on_delete=models.CASCADE)

	class Meta:
		ordering = ['-date_sent']