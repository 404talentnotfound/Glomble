# Generated by Django 5.1.1 on 2024-12-06 14:31

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0061_remove_profile_rating_profile_ratings'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='rating',
            field=models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
