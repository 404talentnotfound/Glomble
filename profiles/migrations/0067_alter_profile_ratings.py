# Generated by Django 5.1.1 on 2024-12-06 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0066_alter_profile_customisation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='ratings',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]