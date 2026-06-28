from django.db import models

# unfinished for now because this update is big enough already lol, try to see if you can guess the concept

class Feedback(models.Model):
    author = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    response_to = models.ForeignKey('Feedback', null=True, on_delete=models.SET_NULL, related_name="previous_feedback")
    feedback = models.TextField(max_length=2500)
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE)
    rating = models.IntegerField()