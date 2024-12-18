# Generated by Django 5.1.1 on 2024-12-05 20:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0057_rename_profilecustomization_profilecustomisation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profilecustomisation',
            name='profile',
        ),
        migrations.AddField(
            model_name='profile',
            name='customisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='profiles.profilecustomisation'),
        ),
        migrations.AddField(
            model_name='profilecustomisation',
            name='customised_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='profiles.profile'),
        ),
    ]
