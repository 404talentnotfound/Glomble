# Generated by Django 5.1.1 on 2024-12-06 21:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0065_alter_profilecustomisation_banner_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='customisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='profiles.profilecustomisation'),
        ),
    ]