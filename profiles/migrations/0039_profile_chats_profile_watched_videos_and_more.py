# Generated by Django 5.1.1 on 2024-11-26 21:36

import profiles.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0016_remove_basenotification_like_notification_and_more'),
        ('profiles', '0038_merge_20241126_2136'),
        ('videos', '0059_remove_comment_reply_comment_replies'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message',
            field=models.TextField(max_length=1000, validators=[profiles.models.validate_characters]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(default='hello, world!', max_length=500, validators=[profiles.models.validate_characters]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='notifications',
            field=models.ManyToManyField(blank=True, related_name='notifications', to='notifications.basenotification'),
        ),
    ]
