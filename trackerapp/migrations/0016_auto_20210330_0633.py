# Generated by Django 3.1.7 on 2021-03-30 06:33

import django.core.validators
from django.db import migrations
import django_resized.forms


class Migration(migrations.Migration):

    dependencies = [
        ('trackerapp', '0015_auto_20210329_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture',
            field=django_resized.forms.ResizedImageField(blank=True, crop=None, force_format='JPEG', keep_meta=True, null=True, quality=75, size=[400, 400], upload_to='uploads/userprofile/', validators=[django.core.validators.validate_image_file_extension]),
        ),
    ]
