# Generated by Django 3.1.7 on 2021-03-23 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trackerapp", "0008_auto_20210323_0855"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="message",
            options={"ordering": ["creation_date"]},
        ),
        migrations.AlterField(
            model_name="message",
            name="creation_date",
            field=models.DateTimeField(auto_created=True, auto_now_add=True),
        ),
    ]
