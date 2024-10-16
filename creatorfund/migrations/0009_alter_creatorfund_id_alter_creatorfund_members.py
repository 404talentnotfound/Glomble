# Generated by Django 5.1.1 on 2024-10-12 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creatorfund', '0008_rename_money_creatorfund_percentage_share_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creatorfund',
            name='id',
            field=models.SlugField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='creatorfund',
            name='members',
            field=models.ManyToManyField(null=True, to='creatorfund.creator'),
        ),
    ]
