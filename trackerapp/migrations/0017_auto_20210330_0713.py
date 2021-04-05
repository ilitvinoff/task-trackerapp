# Generated by Django 3.1.7 on 2021-03-30 07:13

import django.core.validators
import django_resized.forms
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("trackerapp", "0016_auto_20210330_0633"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="picture",
            field=django_resized.forms.ResizedImageField(
                blank=True,
                crop=None,
                force_format=None,
                keep_meta=True,
                null=True,
                quality=75,
                size=[400, 400],
                upload_to="uploads/userprofile/",
                validators=[django.core.validators.validate_image_file_extension],
            ),
        ),
    ]
