# Generated by Django 5.1.1 on 2024-10-10 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0048_alter_comment_comment_alter_video_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='passed_milestones',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='video',
            name='passed_milestones',
            field=models.PositiveIntegerField(default=0),
        ),
    ]