from django.contrib import admin
from .models import NotificationTemplate, NotificationLog


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'is_html', 'is_active', 'created_at')
    list_filter = ('is_html', 'is_active')
    search_fields = ('name', 'subject', 'body')
    ordering = ('-created_at',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'subject', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('recipient', 'subject', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'template', 'recipient', 'subject', 'message',
                       'parameters', 'status', 'error_message', 'created_at')
