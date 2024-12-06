# Generated by Django 5.1.1 on 2024-12-06 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0068_video_recommendation_milestones'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='catagory',
            field=models.CharField(choices=[('Memes', 'MEMES'), ('Games', 'GAMES'), ('Education', 'EDUCATION'), ('Animation', 'ANIMATION'), ('Entertainment', 'ENTERTAINMENT'), ('Music', 'MUSIC'), ('Discussion', 'DISCUSSION'), ('Misc', 'MISCELLANIOUS')], default='Entertainment', max_length=13),
        ),
    ]
