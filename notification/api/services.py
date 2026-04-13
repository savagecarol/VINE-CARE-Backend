import re
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import NotificationTemplate, NotificationLog, StatusType

logger = logging.getLogger(__name__)


def render_template(text: str, parameters: dict) -> str:
    """Replace {{placeholder}} variables in template text."""
    for key, value in (parameters or {}).items():
        pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
        text = re.sub(pattern, str(value), text)
    return text


def _strip_html(html: str) -> str:
    """Very simple HTML → plain text for fallback."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class EmailService:

    @staticmethod
    def send(recipient: str, subject: str, body: str, is_html: bool = False) -> tuple[bool, str]:
        """Send email via SMTP. If is_html=True, sends multipart HTML+text."""
        try:
            if is_html:
                plain = _strip_html(body)
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient],
                )
                msg.attach_alternative(body, 'text/html')
                msg.send(fail_silently=False)
            else:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
            logger.info(f"[EMAIL] Sent to {recipient}: {subject}")
            return True, None
        except Exception as e:
            logger.error(f"[EMAIL] Failed for {recipient}: {e}")
            return False, str(e)


class NotificationService:

    @classmethod
    def send_email(cls, template_name: str, recipient: str, parameters: dict = None) -> dict:
        """
        Send an email using a stored template.
        Returns {'success': bool, 'log_id': str, 'error': str|None}
        """
        try:
            template = NotificationTemplate.objects.get(name=template_name, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.warning(f"[NOTIFY] Template '{template_name}' not found")
            return {'success': False, 'error': f"Template '{template_name}' not found or inactive"}

        subject = render_template(template.subject, parameters)
        body    = render_template(template.body,    parameters)

        success, error_msg = EmailService.send(recipient, subject, body, is_html=template.is_html)

        log = NotificationLog.objects.create(
            template=template,
            recipient=recipient,
            subject=subject,
            message=body,
            parameters=parameters or {},
            status=StatusType.SUCCESS if success else StatusType.FAILED,
            error_message=error_msg,
        )

        return {'success': success, 'log_id': str(log.id), 'error': error_msg}
