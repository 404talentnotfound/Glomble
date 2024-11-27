# Generated by Django 5.1.1 on 2024-10-12 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creatorfund', '0007_remove_creatorfund_members_creatorfund_members'),
    ]

    operations = [
        migrations.RenameField(
            model_name='creatorfund',
            old_name='money',
            new_name='percentage_share',
        ),
        migrations.AddField(
            model_name='creatorfund',
            name='name',
            field=models.CharField(default='greg bog', max_length=50),
            preserve_default=False,
        ),
    ]