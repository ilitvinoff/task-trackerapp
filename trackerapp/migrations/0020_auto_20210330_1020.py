# Generated by Django 3.1.7 on 2021-03-30 10:20

import django.core.validators
import stdimage.validators
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("trackerapp", "0019_auto_20210330_0841"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="picture",
            field=stdimage.models.StdImageField(
                blank=True,
                null=True,
                upload_to="uploads/userprofile/",
                validators=[
                    django.core.validators.validate_image_file_extension,
                    stdimage.validators.MinSizeValidator(200, 200),
                ],
            ),
        ),
    ]
