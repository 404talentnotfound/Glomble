# Generated by Django 5.1.1 on 2024-10-11 08:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0013_messagenotification_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basenotification',
            name='message_notification',
        ),
        migrations.DeleteModel(
            name='MessageNotification',
        ),
    ]