# Generated by Django 4.1.3 on 2022-11-11 08:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_rename_pfp_profile_profile_picture'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ['-date_made']},
        ),
    ]
