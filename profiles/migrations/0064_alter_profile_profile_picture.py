# Generated by Django 5.1.1 on 2024-12-06 20:12

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0063_alter_profile_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_picture',
            field=models.FileField(blank=True, default='profiles/pfps/default.png', help_text='(must be a png or jpg between 1kb and 10mb)', upload_to='media/profiles/pfps/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])]),
        ),
    ]
