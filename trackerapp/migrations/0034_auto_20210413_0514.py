# Generated by Django 3.1.7 on 2021-04-13 05:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('trackerapp', '0033_auto_20210412_1404'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/userprofile/',
                                    validators=[django.core.validators.validate_image_file_extension]),
        ),
    ]
