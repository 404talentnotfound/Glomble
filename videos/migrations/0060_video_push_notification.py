# Generated by Django 5.1.1 on 2024-12-03 08:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0059_remove_comment_reply_comment_replies'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='push_notification',
            field=models.BooleanField(default=True, help_text='would you like your followers to get notifications for this video?', verbose_name='Comment'),
        ),
    ]
