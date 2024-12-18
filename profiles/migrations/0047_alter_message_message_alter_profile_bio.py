# Generated by Django 5.1.1 on 2024-11-26 20:57

import profiles.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0046_alter_message_message_alter_profile_bio'),
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
    ]
