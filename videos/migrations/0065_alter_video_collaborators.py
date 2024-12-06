# Generated by Django 5.1.1 on 2024-12-03 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0051_personalstyle'),
        ('videos', '0064_video_collaborators'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='collaborators',
            field=models.ManyToManyField(blank=True, related_name='video_views', to='profiles.profile'),
        ),
    ]