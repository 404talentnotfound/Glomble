# Generated by Django 5.1.1 on 2024-09-27 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0045_alter_video_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment',
            field=models.CharField(max_length=200),
        ),
    ]
