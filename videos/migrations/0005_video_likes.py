
# Generated by Django 4.1.3 on 2022-11-07 13:27

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('videos', '0004_alter_video_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='likes',
            field=models.ManyToManyField(related_name='video_like', to=settings.AUTH_USER_MODEL),
        ),
    ]

# Generated by Django 4.1.3 on 2022-11-07 13:27

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('videos', '0004_alter_video_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='likes',
            field=models.ManyToManyField(related_name='video_like', to=settings.AUTH_USER_MODEL),
        ),
    ]

