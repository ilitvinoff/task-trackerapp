# Generated by Django 3.1.7 on 2021-03-25 08:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trackerapp", "0009_auto_20210323_1139"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taskmodel",
            name="assignee",
            field=models.ForeignKey(
                blank=True,
                help_text="Select a user who can watch / edit / complete the task",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="taskmodel",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="owned_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
