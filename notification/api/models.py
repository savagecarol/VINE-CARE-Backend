import uuid
from django.db import models


class StatusType(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED  = 'FAILED',  'Failed'


class NotificationTemplate(models.Model):
    """
    Email template with {{placeholder}} variable support.
    Example body: "Hello {{name}}, your report is ready."
    """
    name       = models.CharField(max_length=100, unique=True)
    subject    = models.CharField(max_length=255)
    body       = models.TextField(help_text='Use {{variable}} placeholders. Can be HTML.')
    is_html    = models.BooleanField(default=False, help_text='Send as HTML email')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class NotificationLog(models.Model):
    """Log of every email attempted."""
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template      = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True)
    recipient     = models.CharField(max_length=255)
    subject       = models.CharField(max_length=255, blank=True)
    message       = models.TextField()
    parameters    = models.JSONField(default=dict)
    status        = models.CharField(max_length=20, choices=StatusType.choices, default=StatusType.PENDING)
    error_message = models.TextField(blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Email to {self.recipient} [{self.status}]"
