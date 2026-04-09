from django.db import models
import uuid


class ChannelType(models.TextChoices):
    EMAIL = 'EMAIL', 'Email'
    SMS = 'SMS', 'SMS'
    PUSH = 'PUSH', 'Push Notification'


class StatusType(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'


class NotificationTemplate(models.Model):
    """
    Template for notifications with placeholders.
    Placeholders should be in format: {{variable_name}}
    Example: "Hello {{username}}, your account has been created with ${{amount}}"
    """
    name = models.CharField(max_length=100, unique=True, help_text='Unique template identifier')
    channel = models.CharField(max_length=20, choices=ChannelType.choices)
    subject = models.CharField(max_length=255, blank=True, help_text='Subject for emails (optional for SMS/Push)')
    body = models.TextField(help_text='Template body with {{placeholder}} variables')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'channel']

    def __str__(self):
        return f"{self.name} ({self.channel})"


class NotificationLog(models.Model):
    """
    Log of all notifications sent.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True)
    channel = models.CharField(max_length=20, choices=ChannelType.choices)
    recipient = models.CharField(max_length=255, help_text='Email, phone number, or device token')
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    parameters = models.JSONField(default=dict, help_text='Dynamic parameters used')
    status = models.CharField(max_length=20, choices=StatusType.choices, default=StatusType.PENDING)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.channel} to {self.recipient} [{self.status}]"


class DeviceToken(models.Model):
    """
    Device tokens for push notifications.
    Users can have multiple devices.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(help_text='Reference to user ID from Data Collection service')
    device_token = models.CharField(max_length=512, help_text='FCM/APNs device token')
    platform = models.CharField(max_length=20, choices=[('IOS', 'iOS'), ('ANDROID', 'Android')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user_id', 'device_token']

    def __str__(self):
        return f"{self.platform} device for user {self.user_id}"