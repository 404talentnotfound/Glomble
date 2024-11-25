# Generated by Django 5.1.1 on 2024-11-24 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0036_alter_profile_notifications'),
        ('videos', '0054_remove_video_suggestions_video_recommendations'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='watched_videos',
            field=models.ManyToManyField(related_name='notifications', to='videos.video'),
        ),
    ]
