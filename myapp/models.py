from django.db import models
from django.utils import timezone
import random
from django.contrib.auth.models import User

class Device(models.Model):
    DEVICE_TYPES = [
        ('Temperature Sensor', 'Temperature Sensor'),
        ('Humidity Sensor', 'Humidity Sensor'),
        ('Motion Sensor', 'Motion Sensor'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Inactive')
    last_reading = models.JSONField(null=True, blank=True)  # Stores the last sensor reading
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SensorData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_random_data(sensor_type):
        if sensor_type.lower() == 'temperature sensor':
            return round(random.uniform(20, 30), 2)
        elif sensor_type.lower() == 'humidity sensor':
            return round(random.uniform(40, 60), 2)
        elif sensor_type.lower() == 'motion sensor':
            return random.randint(0, 1)
        return None
 
