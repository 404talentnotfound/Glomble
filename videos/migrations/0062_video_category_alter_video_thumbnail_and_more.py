# Generated by Django 5.1.1 on 2024-12-06 21:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0061_video_recommendation_milestones_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='category',
            field=models.CharField(choices=[('Memes', 'Memes'), ('Gaming', 'Gaming'), ('Education', 'Education'), ('Animation', 'Animation'), ('Entertainment', 'Entertainment'), ('Music', 'Music'), ('Discussion', 'Discussion'), ('Misc', 'Miscellanious')], default='Entertainment', max_length=13),
        ),
        migrations.AlterField(
            model_name='video',
            name='thumbnail',
            field=models.FileField(blank=True, help_text='(must be a png or jpg between 1kb and 10mb)', upload_to='uploads/thumbnails/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])]),
        ),
        migrations.AlterField(
            model_name='video',
            name='video_file',
            field=models.FileField(help_text='(must be an mp4 or mov between 1kb and 5gb and be under 2 hours)', upload_to='uploads/video_files/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['mp4', 'mov'])]),
        ),
    ]
