# Generated by Django 3.1.7 on 2021-05-17 11:39

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0009_auto_20210514_1107'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessagemodel',
            name='backup_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name='chatroommodel',
            name='backup_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
