import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import NotificationTemplate, NotificationLog
from .services import NotificationService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok', 'service': 'notification'})


@api_view(['POST'])
@permission_classes([AllowAny])
def send_email(request):
    """
    Send an email using a stored template.

    POST /api/send/
    {
        "template_name": "welcome",
        "recipient": "user@example.com",
        "parameters": { "name": "John" }
    }
    """
    template_name = request.data.get('template_name')
    recipient     = request.data.get('recipient')
    parameters    = request.data.get('parameters', {})

    if not template_name:
        return Response({'error': 'template_name is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not recipient:
        return Response({'error': 'recipient is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(parameters, dict):
        return Response({'error': 'parameters must be a JSON object'}, status=status.HTTP_400_BAD_REQUEST)

    result = NotificationService.send_email(template_name, recipient, parameters)

    if result['success']:
        return Response({'message': 'Email sent', 'log_id': result['log_id']})
    return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_template(request):
    """
    Create or update an email template.

    POST /api/template/
    {
        "name": "welcome",
        "subject": "Welcome {{name}}!",
        "body": "Hello {{name}}, welcome to VineCare."
    }
    """
    name    = request.data.get('name')
    subject = request.data.get('subject')
    body    = request.data.get('body')

    if not name or not subject or not body:
        return Response({'error': 'name, subject, and body are required'}, status=status.HTTP_400_BAD_REQUEST)

    template, created = NotificationTemplate.objects.update_or_create(
        name=name,
        defaults={'subject': subject, 'body': body, 'is_active': True},
    )

    return Response({
        'message': 'Template created' if created else 'Template updated',
        'template': {'id': template.id, 'name': template.name, 'subject': template.subject},
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_templates(request):
    """
    GET /api/templates/
    """
    templates = NotificationTemplate.objects.filter(is_active=True)
    return Response({'templates': [
        {'id': t.id, 'name': t.name, 'subject': t.subject, 'created_at': t.created_at.isoformat()}
        for t in templates
    ]})


@api_view(['GET'])
@permission_classes([AllowAny])
def notification_logs(request):
    """
    GET /api/logs/
    Query params: status (SUCCESS|FAILED|PENDING), page, limit
    """
    qs     = NotificationLog.objects.all()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter.upper())

    page  = max(1, int(request.query_params.get('page',  1)))
    limit = max(1, int(request.query_params.get('limit', 20)))
    total = qs.count()
    logs  = qs[(page - 1) * limit : page * limit]

    return Response({
        'page': page, 'limit': limit, 'total': total,
        'total_pages': (total + limit - 1) // limit,
        'results': [
            {
                'id':         str(log.id),
                'recipient':  log.recipient,
                'subject':    log.subject,
                'status':     log.status,
                'error':      log.error_message,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ],
    })
