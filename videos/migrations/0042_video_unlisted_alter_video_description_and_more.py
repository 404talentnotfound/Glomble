# Generated by Django 5.1.1 on 2024-09-25 18:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0041_alter_comment_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='unlisted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='video',
            name='description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='id',
            field=models.SlugField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='video',
            name='thumbnail',
            field=models.FileField(blank=True, upload_to='media/uploads/thumbnails/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])]),
        ),
        migrations.AlterField(
            model_name='video',
            name='title',
            field=models.CharField(max_length=50),
        ),
    ]