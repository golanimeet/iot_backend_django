from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Device, SensorData
from .serializers import DeviceSerializer, SensorDataSerializer
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes
from django.utils.timezone import now, timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
import threading, time
import logging

logger = logging.getLogger(__name__)

# Register, Login, Password Reset Request, Password Reset Confirm
class RegisterView(APIView):
    def post(self, request):
        data = request.data
        if data.get('password') != data.get('confirmPassword'):
            return Response({'detail': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=data.get('email')).exists():
            return Response({'detail': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(
            username=data.get('email'),  # Use email as username for simplicity
            email=data.get('email'),
            first_name=data.get('firstName'),
            last_name=data.get('lastName'),
            password=data.get('password')
        )
        return Response({'detail': 'User registered successfully'}, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    def post(self, request):
        data = request.data
        user = authenticate(username=data.get('email'), password=data.get('password'))
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {  # Include user details in response
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        logger.info("Processing password reset request for email: %s", email)

        if not email:
            return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.info("Password reset requested for non-existent email: %s", email)
            return Response({'detail': 'If your email is registered, you will receive a reset link.'}, status=status.HTTP_200_OK)

        # Generate reset link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"http://localhost:4200/reset-password/{uid}/{token}"

        context = {'reset_url': reset_url, 'user': user}
        html_content = render_to_string('emails/reset-password.html', context)
        text_content = f"Reset your password here: {reset_url}"

        try:
            email_message = EmailMultiAlternatives(
                subject="Password Reset Request",
                body=text_content,
                from_email="noreply@example.com",
                to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            logger.info("Password reset email sent successfully to %s", email)
            return Response({'detail': 'Password reset email sent successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Email sending failed: %s", e)
            return Response({'detail': 'Failed to send password reset email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PasswordResetConfirmView(APIView):
    def post(self, request):
        # Log the incoming request body to see what is being sent
        logger.info("Request Data: %s", request.data)

        # Retrieve the fields from the request data
        uidb64 = request.data.get('uidb64')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        # Check if any of the required fields are missing
        if not all([uidb64, token, new_password]):
            logger.warning("Missing fields. uidb64: %s, token: %s, new_password: %s", uidb64, token, new_password)
            return Response({'detail': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError) as e:
            logger.error("Error decoding UID or fetching user: %s", e)
            return Response({'detail': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            logger.error("Invalid or expired token for user %s", user.email)
            return Response({'detail': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        logger.info("Password successfully reset for user %s", user.email)
        return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)


# Device get and post data
class DeviceListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        devices = Device.objects.filter(user=request.user)  # Get devices for the logged-in user
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id # Automatically associate the device with the logged-in user
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Device Detail View for getting, updating, and deleting a single device by ID
class DeviceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = DeviceSerializer(device)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = DeviceSerializer(device, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        device.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def generate_sensor_data(device):
    # """Continuously generates sensor data every minute while the device is active."""
    while Device.objects.filter(id=device.id, status="Active").exists():
        sensor_value = SensorData.generate_random_data(device.type)
        SensorData.objects.create(device=device, type=device.type, value=sensor_value)
        device.last_reading = {'value': sensor_value}
        device.save()
        time.sleep(60)  # Wait for 1 minute


@csrf_exempt  # Cross-Site Request Forgery use protection for a particular view
def toggle_device_status(request, device_id):
    if request.method == 'POST':
        try:
            device = Device.objects.get(id=device_id)
            if device.status == 'Inactive':
                device.status = 'Active'
                device.save()

                # Threads are typically used to handle multiple tasks
                thread = threading.Thread(target=generate_sensor_data, args=(device,))
                thread.daemon = True
                thread.start()
                
            else:
                device.status = 'Inactive'
                # device.last_reading = None
                device.save()

            return JsonResponse({'status': 'success', 'device_status': device.status, 'last_reading': device.last_reading})
        except Device.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Device not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


class ReportDataView(APIView):
    def get(self, request):
        device_name = request.query_params.get('device_name')
        date_range = request.query_params.get('date_range')
        if not device_name or not date_range:
            return JsonResponse({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(name=device_name)
            end_date = timezone.now()
            if date_range == 'daily':
                start_date = end_date - timedelta(days=1)
            elif date_range == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            elif date_range == 'monthly':
                start_date = end_date - timedelta(days=30)

            data = SensorData.objects.filter(device=device, timestamp__range=[start_date, end_date])
            serializer = SensorDataSerializer(data, many=True)
            return JsonResponse(serializer.data, safe=False)
        except Device.DoesNotExist:
            return JsonResponse({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)
        

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        device_name = request.query_params.get("device_name")
        date_range = request.query_params.get("date_range")

        # Filter total devices by logged-in user
        total_devices = Device.objects.filter(user=request.user).count()
        total_reports = SensorData.objects.filter(device__user=request.user).count()

        # Initialize selected device stats
        selected_device_id = 0
        selected_device_value = 0

        # Filter by device name
        if device_name:
            try:
                device = Device.objects.get(name=device_name, user=request.user)
                selected_device_id = device.id
            except Device.DoesNotExist:
                return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)

            filtered_data = SensorData.objects.filter(device=device)

            # Filter by date range
            if date_range == "daily":
                start_date = now() - timedelta(days=1)
            elif date_range == "weekly":
                start_date = now() - timedelta(weeks=1)
            elif date_range == "monthly":
                start_date = now() - timedelta(days=30)
            else:
                start_date = None

            if start_date:
                filtered_data = filtered_data.filter(timestamp__gte=start_date)

            selected_device_value = filtered_data.count()

        return Response({
            "totalDevices": total_devices,
            "totalSensore": total_reports,
            "selectedDeviceId": selected_device_id,
            "selectedDeviceValue": selected_device_value
        }, status=status.HTTP_200_OK)
    

        
# class DashboardStatsView(APIView):
#     permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

#     def get(self, request):
#         # Filter by the logged-in user
#         total_devices = Device.objects.filter(user=request.user).count()
#         total_reports = SensorData.objects.filter(device__user=request.user).count()

#         return Response({
#             "totalDevices": total_devices,
#             "totalSensore": total_reports
#         }, status=status.HTTP_200_OK)
