from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Device, SensorData
from django.contrib.auth.tokens import default_token_generator

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, data):
        # Check if password and password2 match
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'password2': 'Password and Confirm Password do not match.'
            })

        # Return validated data
        return data

    def create(self, validated_data):
        validated_data.pop('password2')  # Remove password2 from data
        user = User.objects.create_user(**validated_data)  # Create user
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Use the built-in User model
        fields = ['id', 'username', 'email', 'first_name', 'last_name']  # Include desired fields



class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'



class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = '__all__'

