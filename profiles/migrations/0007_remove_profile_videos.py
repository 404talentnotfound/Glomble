# Generated by Django 4.1.3 on 2022-11-12 16:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_profile_videos'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='videos',
        ),
    ]
