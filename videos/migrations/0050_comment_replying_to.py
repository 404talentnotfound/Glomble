# Generated by Django 5.1.1 on 2024-10-13 15:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0049_comment_passed_milestones_video_passed_milestones'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='replying_to',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='videos.comment'),
        ),
    ]
