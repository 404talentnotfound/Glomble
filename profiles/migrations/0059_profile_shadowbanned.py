# Generated by Django 5.1.1 on 2024-12-05 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0058_remove_profilecustomisation_profile_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='shadowbanned',
            field=models.BooleanField(default=False),
        ),
    ]
