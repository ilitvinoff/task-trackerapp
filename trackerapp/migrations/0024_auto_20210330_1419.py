# Generated by Django 3.1.7 on 2021-03-30 14:19

import django.core.validators
from django.db import migrations
import stdimage.models
import stdimage.validators


class Migration(migrations.Migration):

    dependencies = [
        ('trackerapp', '0023_auto_20210330_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture',
            field=stdimage.models.StdImageField(blank=True, null=True, upload_to='uploads/userprofile/', validators=[django.core.validators.validate_image_file_extension, stdimage.validators.MinSizeValidator(200, 200)]),
        ),
    ]
