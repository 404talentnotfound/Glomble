# Generated by Django 5.1.1 on 2024-10-10 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0010_follownotification_follower_likenotification_liker'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follownotification',
            name='follower',
        ),
        migrations.RemoveField(
            model_name='likenotification',
            name='liker',
        ),
    ]