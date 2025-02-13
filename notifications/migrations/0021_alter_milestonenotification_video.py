# Generated by Django 5.1.1 on 2024-12-06 13:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0020_alter_milestonenotification_video'),
        ('videos', '0061_video_recommendation_milestones_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='milestonenotification',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='milestone_video', to='videos.video'),
        ),
    ]
