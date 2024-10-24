# Generated by Django 5.1.1 on 2024-10-11 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0032_profileactivity_searches'),
        ('videos', '0049_comment_passed_milestones_video_passed_milestones'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileactivity',
            name='disliked_videos',
            field=models.ManyToManyField(related_name='disliked_videos', to='videos.video'),
        ),
    ]
