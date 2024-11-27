# Generated by Django 5.1.1 on 2024-11-26 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0057_video_comments_alter_comment_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='reply',
            field=models.ManyToManyField(blank=True, related_name='replies', to='videos.comment'),
        ),
    ]