# Generated by Django 3.1.7 on 2021-03-30 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackerapp', '0020_auto_20210330_1020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/userprofile/'),
        ),
    ]
