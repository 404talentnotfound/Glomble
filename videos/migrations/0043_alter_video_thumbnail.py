# Generated by Django 5.1.1 on 2024-09-27 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0042_video_unlisted_alter_video_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to='media/uploads/thumbnails/'),
        ),
    ]