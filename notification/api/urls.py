from django.urls import path
from . import views

urlpatterns = [
    # Main notification endpoint
    path('send/', views.send_notification, name='send_notification'),

    # Device token management
    path('device/register/', views.register_device, name='register_device'),

    # Template management
    path('template/', views.create_template, name='create_template'),
    path('templates/', views.list_templates, name='list_templates'),

    # Logs
    path('logs/', views.notification_logs, name='notification_logs'),

    # Health check
    path('health/', views.health_check, name='health_check'),
]