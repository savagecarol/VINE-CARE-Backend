import re
import logging
from .models import (
    ChannelType, TriggerEvent,
    NotificationTemplate, Notification,
    EmailNotification, SMSNotification
)

logger = logging.getLogger(__name__)


def render_template(template_text: str, payload: dict) -> str:
    for key, value in payload.items():
        template_text = re.sub(rf"{{\s*{key}\s*}}", str(value), template_text)
    return template_text


class NotificationService:

    @staticmethod
    def _send_app(user_id, template, payload):
        message = render_template(template.template, payload)
        Notification.objects.create(
            user_id=user_id,
            template=template,
            payload=payload,
            message=message,
        )
        logger.info(f"[APP] Notification sent to user {user_id}")

    @staticmethod
    def _send_email(user_id, template, payload):
        message = render_template(template.template, payload)
        notif = EmailNotification.objects.create(
            user_id=user_id,
            template=template,
            payload=payload,
            message=message,
        )
        try:
            # Replace with real email logic e.g. Django send_mail()
            logger.info(f"[EMAIL] Sending to user {user_id}: {message}")
            notif.status = "SUCCESS"
        except Exception as e:
            notif.status = "FAILED"
            notif.status_reason = str(e)
        notif.save()

    @staticmethod
    def _send_sms(user_id, template, payload):
        message = render_template(template.template, payload)
        notif = SMSNotification.objects.create(
            user_id=user_id,
            template=template,
            payload=payload,
            message=message,
        )
        try:
            # Replace with real SMS logic e.g. Twilio
            logger.info(f"[SMS] Sending to user {user_id}: {message}")
            notif.status = "SUCCESS"
        except Exception as e:
            notif.status = "FAILED"
            notif.status_reason = str(e)
        notif.save()

    @classmethod
    def notify(cls, user_id: int, event: str, payload: dict):
        templates = NotificationTemplate.objects.filter(
            trigger_event=event,
            is_active=True
        )

        if not templates.exists():
            logger.warning(f"No active template found for event: {event}")
            return

        for template in templates:
            if template.channel == ChannelType.APP:
                cls._send_app(user_id, template, payload)
            elif template.channel == ChannelType.EMAIL:
                cls._send_email(user_id, template, payload)
            elif template.channel == ChannelType.SMS:
                cls._send_sms(user_id, template, payload)