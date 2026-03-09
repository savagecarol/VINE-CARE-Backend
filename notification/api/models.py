from django.db import models

# Create your models here.

import uuid
import re
from django.db import models


class ChannelType(models.TextChoices):
    APP = 'APP', 'In-App Notification'
    SMS = 'SMS', 'SMS'
    EMAIL = 'EMAIL', 'Email'


class TriggerEvent(models.TextChoices):
    ENROLLMENT = 'ENROLLMENT', 'Enrollment'
    ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
    RESET_PASSWORD = 'RESET_PASSWORD', 'Reset Password'


class StatusType(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'


class NotificationTemplate(models.Model):
    title = models.CharField(max_length=255)
    template = models.TextField(help_text='Use placeholders like {{username}}')
    channel = models.CharField(max_length=20, choices=ChannelType.choices, default=ChannelType.APP)
    trigger_event = models.CharField(max_length=50, choices=TriggerEvent.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.channel})"


class Notification(models.Model):
    user_id = models.UUIDField()
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    payload = models.JSONField(default=dict)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for user {self.user_id}"


class EmailNotification(models.Model):
    user_id = models.UUIDField()
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    payload = models.JSONField(default=dict)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=StatusType.choices, default=StatusType.PENDING)
    status_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email to user {self.user_id} [{self.status}]"


class SMSNotification(models.Model):
    user_id = models.UUIDField()
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    payload = models.JSONField(default=dict)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=StatusType.choices, default=StatusType.PENDING)
    status_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS to user {self.user_id} [{self.status}]"