# Generated by Django 3.1.7 on 2021-04-28 12:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('trackerapp', '0043_auto_20210428_0603'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachment',
            options={'ordering': ['-creation_date']},
        ),
    ]
