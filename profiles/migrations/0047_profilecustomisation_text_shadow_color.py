# Generated by Django 5.1.1 on 2025-01-22 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0046_alter_profile_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilecustomisation',
            name='text_shadow_color',
            field=models.CharField(default='#FFFFFF', help_text='Text shadow color in hex.', max_length=7),
        ),
    ]
