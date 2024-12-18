# Generated by Django 5.1.1 on 2024-12-03 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0060_video_push_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='push_notification',
            field=models.BooleanField(default=True, help_text='would you like your followers to get notifications for this video?'),
        ),
    ]
