# Generated by Django 3.1.7 on 2021-04-08 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackerapp', '0030_auto_20210406_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskmodel',
            name='status',
            field=models.CharField(choices=[('waiting to start', 'waiting to start'), ('in work', 'in work'), ('completed', 'completed')], default='waiting to start', help_text='Current task status', max_length=16),
        ),
    ]
