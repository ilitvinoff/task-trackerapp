# Generated by Django 3.1.7 on 2021-05-14 11:07

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0008_auto_20210507_0607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatroommodel',
            name='member',
            field=models.ManyToManyField(blank=True, related_name='member', to=settings.AUTH_USER_MODEL),
        ),
    ]
