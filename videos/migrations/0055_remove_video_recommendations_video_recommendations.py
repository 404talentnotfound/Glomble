# Generated by Django 5.1.1 on 2024-11-24 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0054_remove_video_suggestions_video_recommendations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='recommendations',
        ),
        migrations.AddField(
            model_name='video',
            name='recommendations',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
