from django.urls import path
from .views import RegisterView, LoginView, PasswordResetRequestView, PasswordResetConfirmView, DeviceListView, DeviceDetailView, ReportDataView, DashboardStatsView, toggle_device_status

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('devices/', DeviceListView.as_view(), name='device-list'),
    path('devices/<int:device_id>/', DeviceDetailView.as_view(), name='device-detail'),
    path('toggle-device-status/<int:device_id>/', toggle_device_status, name='toggle_device_status'),
    path('report-data/', ReportDataView.as_view(), name='report-data'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
