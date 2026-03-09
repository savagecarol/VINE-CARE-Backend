import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Notification, TriggerEvent
from .services import NotificationService


@api_view(['POST'])
def send_notification(request):
    """
    POST /api/notify/
    Body: { "user_id": "550e8400-e29b-41d4-a716-446655440000", "event": "ENROLLMENT", "payload": {"username": "John"} }
    """
    user_id = request.data.get('user_id')
    event = request.data.get('event')
    payload = request.data.get('payload', {})

    if not user_id or not event:
        return Response({'error': 'user_id and event are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = uuid.UUID(str(user_id))
    except ValueError:
        return Response({'error': 'Invalid user_id, must be a valid UUID'}, status=status.HTTP_400_BAD_REQUEST)

    if event not in TriggerEvent.values:
        return Response({'error': f'Invalid event. Choices: {TriggerEvent.values}'}, status=status.HTTP_400_BAD_REQUEST)

    NotificationService.notify(user_id=user_id, event=event, payload=payload)
    return Response({'message': 'Notification sent'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_user_notifications(request, user_id):
    """
    GET /api/notifications/<user_id>/
    """
    notifications = Notification.objects.filter(
        user_id=user_id
    ).order_by('-created_at').values('id', 'message', 'is_read', 'created_at')

    return Response(list(notifications))


@api_view(['PATCH'])
def mark_as_read(request, pk):
    """
    PATCH /api/notifications/<pk>/read/
    """
    try:
        notif = Notification.objects.get(pk=pk)
        notif.is_read = True
        notif.save()
        return Response({'message': 'Marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)