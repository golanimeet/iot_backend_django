from .models import Device, SensorData
from django.contrib import admin

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'type', 'status', 'last_reading', 'created_at', 'updated_at')  # Customize the columns displayed
    search_fields = ('name', 'type')
    
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'type', 'value', 'timestamp')  # Customize the columns displayed
    search_fields = ['device__name', 'type']

admin.site.register(Device, DeviceAdmin)
admin.site.register(SensorData, SensorDataAdmin)