# Generated by Django 5.1.1 on 2024-12-03 20:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0053_alter_profile_profile_picture'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='passed_milestones',
            new_name='follower_milestones',
        ),
    ]
