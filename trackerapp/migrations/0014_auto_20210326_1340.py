# Generated by Django 3.1.7 on 2021-03-26 13:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trackerapp", "0013_auto_20210326_1326"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="picture",
            field=models.ImageField(
                blank=True, null=True, upload_to="uploads/userprofile/"
            ),
        ),
    ]
