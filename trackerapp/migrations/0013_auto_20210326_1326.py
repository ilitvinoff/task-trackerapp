# Generated by Django 3.1.7 on 2021-03-26 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trackerapp", "0012_auto_20210325_1158"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="picture",
            field=models.ImageField(blank=True, upload_to="uploads/userprofile/"),
        ),
    ]
