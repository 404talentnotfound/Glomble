# Generated by Django 5.1.1 on 2024-11-24 21:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0039_profile_last_recommend'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='last_recommend',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 1, 1, 1)),
        ),
    ]