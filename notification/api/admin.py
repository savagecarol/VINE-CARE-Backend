from django.contrib import admin
from .models import NotificationTemplate, NotificationLog, DeviceToken


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'subject', 'is_active', 'created_at')
    list_filter = ('channel', 'is_active')
    search_fields = ('name', 'subject', 'body')
    ordering = ('-created_at',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'channel', 'recipient', 'status', 'created_at')
    list_filter = ('channel', 'status')
    search_fields = ('recipient', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'template', 'channel', 'recipient', 'subject', 'message', 'parameters', 'status', 'error_message', 'created_at')


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'platform', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('user_id', 'device_token')
    ordering = ('-created_at',)