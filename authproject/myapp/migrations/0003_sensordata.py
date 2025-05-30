# Generated by Django 5.1.4 on 2025-01-23 09:55

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_alter_device_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SensorData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('Temperature', 'Temperature'), ('Humidity', 'Humidity'), ('Motion', 'Motion')], max_length=50)),
                ('value', models.FloatField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sensor_data', to='myapp.device')),
            ],
        ),
    ]
