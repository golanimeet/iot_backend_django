# Generated by Django 5.1.4 on 2025-01-28 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_device_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='user',
            field=models.CharField(max_length=50),
        ),
    ]
