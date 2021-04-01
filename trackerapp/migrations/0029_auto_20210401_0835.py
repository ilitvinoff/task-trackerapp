# Generated by Django 3.1.7 on 2021-04-01 08:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('trackerapp', '0028_taskmodel_attachment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskmodel',
            name='attachment',
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(auto_created=True, auto_now_add=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='attachments/')),
                ('description', models.TextField(help_text='Enter a brief description of the task.', max_length=1000)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attachment_owner', to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trackerapp.taskmodel')),
            ],
            options={
                'ordering': ['creation_date'],
            },
        ),
    ]
