# Generated by Django 3.1.7 on 2021-04-08 15:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('trackerapp', '0031_auto_20210408_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='body',
            field=models.CharField(help_text='enter message body', max_length=1000),
        ),
    ]