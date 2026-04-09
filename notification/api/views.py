import uuid
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from .models import NotificationTemplate, NotificationLog, DeviceToken, ChannelType
from .services import NotificationService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_notification(request):
    """
    Generic endpoint to send notifications via different channels.

    POST /api/send/
    Request Body:
    {
        "channel": "EMAIL",           # EMAIL, SMS, or PUSH
        "template_name": "welcome",   # Template name
        "recipient": "user@email.com", # Email or phone number (optional for PUSH if user_id provided)
        "user_id": "uuid",            # User ID for PUSH (to look up device tokens)
        "parameters": {                # Dynamic values to replace in template
            "name": "John",
            "amount": "100"
        }
    }

    Templates use {{placeholder}} syntax.
    Example template: "Hello {{name}}, your account has ${{amount}}"
    """
    channel = request.data.get('channel', '').upper()
    template_name = request.data.get('template_name')
    recipient = request.data.get('recipient')
    user_id = request.data.get('user_id')
    parameters = request.data.get('parameters', {})

    # Validation
    if not channel:
        return Response({'error': 'channel is required (EMAIL, SMS, PUSH)'}, status=status.HTTP_400_BAD_REQUEST)

    if channel not in ChannelType.values:
        return Response({'error': f'Invalid channel. Choices: {ChannelType.values}'}, status=status.HTTP_400_BAD_REQUEST)

    if not template_name:
        return Response({'error': 'template_name is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(parameters, dict):
        return Response({'error': 'parameters must be a dictionary'}, status=status.HTTP_400_BAD_REQUEST)

    if user_id:
        try:
            user_id = uuid.UUID(str(user_id))
        except ValueError:
            return Response({'error': 'Invalid user_id format'}, status=status.HTTP_400_BAD_REQUEST)

    # Send notification
    result = NotificationService.send_notification(
        channel=channel,
        template_name=template_name,
        parameters=parameters,
        recipient=recipient,
        user_id=str(user_id) if user_id else None
    )

    if result.get('success'):
        return Response({
            'message': 'Notification sent successfully',
            'data': result
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'message': 'Failed to send notification',
            'error': result.get('error'),
            'data': result
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_device(request):
    """
    Register a device token for push notifications.

    POST /api/device/register/
    Request Body:
    {
        "user_id": "uuid",
        "device_token": "fcm_or_apns_token",
        "platform": "ANDROID"  # IOS or ANDROID
    }
    """
    user_id = request.data.get('user_id')
    device_token = request.data.get('device_token')
    platform = request.data.get('platform', '').upper()

    if not user_id or not device_token or not platform:
        return Response({
            'error': 'user_id, device_token, and platform are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if platform not in ['IOS', 'ANDROID']:
        return Response({'error': 'platform must be IOS or ANDROID'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = uuid.UUID(str(user_id))
    except ValueError:
        return Response({'error': 'Invalid user_id format'}, status=status.HTTP_400_BAD_REQUEST)

    result = NotificationService.register_device_token(
        user_id=str(user_id),
        device_token=device_token,
        platform=platform
    )

    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_template(request):
    """
    Create a notification template.

    POST /api/template/
    Request Body:
    {
        "name": "welcome",
        "channel": "EMAIL",
        "subject": "Welcome {{name}}!",
        "body": "Hello {{name}}, welcome to our service!"
    }
    """
    name = request.data.get('name')
    channel = request.data.get('channel', '').upper()
    subject = request.data.get('subject', '')
    body = request.data.get('body')

    if not name or not channel or not body:
        return Response({'error': 'name, channel, and body are required'}, status=status.HTTP_400_BAD_REQUEST)

    if channel not in ChannelType.values:
        return Response({'error': f'Invalid channel. Choices: {ChannelType.values}'}, status=status.HTTP_400_BAD_REQUEST)

    if channel == 'EMAIL' and not subject:
        return Response({'error': 'subject is required for EMAIL channel'}, status=status.HTTP_400_BAD_REQUEST)

    template, created = NotificationTemplate.objects.get_or_create(
        name=name,
        channel=channel,
        defaults={
            'subject': subject,
            'body': body
        }
    )

    if not created:
        # Update existing template
        template.subject = subject
        template.body = body
        template.is_active = True
        template.save()

    return Response({
        'message': 'Template created' if created else 'Template updated',
        'template': {
            'id': template.id,
            'name': template.name,
            'channel': template.channel,
            'subject': template.subject,
            'body': template.body
        }
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_templates(request):
    """
    List all notification templates.

    GET /api/templates/
    Optional query params:
    - channel: Filter by channel (EMAIL, SMS, PUSH)
    - active_only: true/false (default: true)
    """
    channel = request.query_params.get('channel')
    active_only = request.query_params.get('active_only', 'true').lower() == 'true'

    queryset = NotificationTemplate.objects.all()

    if channel:
        queryset = queryset.filter(channel=channel.upper())

    if active_only:
        queryset = queryset.filter(is_active=True)

    templates = [
        {
            'id': t.id,
            'name': t.name,
            'channel': t.channel,
            'subject': t.subject,
            'body': t.body,
            'is_active': t.is_active,
            'created_at': t.created_at.isoformat()
        }
        for t in queryset
    ]

    return Response({'templates': templates})


@api_view(['GET'])
@permission_classes([AllowAny])
def notification_logs(request):
    """
    Get notification logs.

    GET /api/logs/
    Optional query params:
    - channel: Filter by channel
    - status: Filter by status (PENDING, SUCCESS, FAILED)
    - page: Page number (default: 1)
    - limit: Results per page (default: 20)
    """
    channel = request.query_params.get('channel')
    log_status = request.query_params.get('status')
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))

    queryset = NotificationLog.objects.all()

    if channel:
        queryset = queryset.filter(channel=channel.upper())

    if log_status:
        queryset = queryset.filter(status=log_status.upper())

    total = queryset.count()
    offset = (page - 1) * limit
    logs = queryset[offset:offset + limit]

    data = [
        {
            'id': str(log.id),
            'channel': log.channel,
            'recipient': log.recipient[:30] + '...' if len(log.recipient) > 30 else log.recipient,
            'subject': log.subject,
            'message': log.message[:100] + '...' if len(log.message) > 100 else log.message,
            'status': log.status,
            'created_at': log.created_at.isoformat()
        }
        for log in logs
    ]

    return Response({
        'page': page,
        'limit': limit,
        'total': total,
        'total_pages': (total + limit - 1) // limit,
        'results': data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({'status': 'ok', 'service': 'notification'})