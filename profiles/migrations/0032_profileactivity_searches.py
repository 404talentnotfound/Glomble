# Generated by Django 5.1.1 on 2024-10-11 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0031_profile_using_activity_alter_profile_followers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileactivity',
            name='searches',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]