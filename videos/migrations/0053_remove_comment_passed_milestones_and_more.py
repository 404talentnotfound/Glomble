# Generated by Django 5.1.1 on 2024-11-24 19:11

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0052_comment_replying_to'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='passed_milestones',
        ),
        migrations.RemoveField(
            model_name='video',
            name='passed_milestones',
        ),
        migrations.AddField(
            model_name='video',
            name='suggestions',
            field=models.ManyToManyField(blank=True, related_name='video_suggestions', to=settings.AUTH_USER_MODEL),
        ),
    ]
