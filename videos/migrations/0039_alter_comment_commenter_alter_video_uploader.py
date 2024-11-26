# Generated by Django 4.2.5 on 2023-09-29 12:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0011_alter_profile_username'),
        ('videos', '0038_alter_comment_commenter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='commenter',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='profiles.profile'),
        ),
        migrations.AlterField(
            model_name='video',
            name='uploader',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='profiles.profile'),
        ),
    ]
