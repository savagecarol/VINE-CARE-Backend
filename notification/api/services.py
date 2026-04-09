import re
import logging
import json
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import boto3
from botocore.exceptions import ClientError
from .models import (
    ChannelType, StatusType,
    NotificationTemplate, NotificationLog, DeviceToken
)

logger = logging.getLogger(__name__)


def render_template(template_text: str, parameters: dict) -> str:
    """
    Replace {{placeholder}} variables in template with actual values.
    Example: "Hello {{name}}" with {"name": "John"} -> "Hello John"
    """
    if not parameters:
        return template_text

    for key, value in parameters.items():
        template_text = re.sub(rf"\{{\s*{key}\s*\}}", str(value), template_text)

    return template_text


class AWSService:
    """
    AWS service clients for SES (email) and SNS (SMS/Push).
    """
    _ses_client = None
    _sns_client = None

    @classmethod
    def get_ses_client(cls):
        if cls._ses_client is None:
            cls._ses_client = boto3.client(
                'ses',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return cls._ses_client

    @classmethod
    def get_sns_client(cls):
        if cls._sns_client is None:
            cls._sns_client = boto3.client(
                'sns',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return cls._sns_client


class NotificationService:
    """
    Main notification service that handles sending notifications
    via different channels (Email, SMS, Push).
    """

    @staticmethod
    def _send_email(recipient: str, subject: str, body: str) -> tuple[bool, str]:
        """
        Send email via AWS SES.
        Returns: (success: bool, error_message: str)
        """
        try:
            client = AWSService.get_ses_client()
            client.send_email(
                Source=settings.AWS_SES_SENDER_EMAIL,
                Destination={'ToAddresses': [recipient]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )
            logger.info(f"[EMAIL] Sent to {recipient}")
            return True, None
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            logger.error(f"[EMAIL] Failed to send to {recipient}: {error_msg}")
            return False, error_msg
        except Exception as e:
            logger.error(f"[EMAIL] Unexpected error for {recipient}: {str(e)}")
            return False, str(e)

    @staticmethod
    def _send_sms(phone_number: str, message: str) -> tuple[bool, str]:
        """
        Send SMS via AWS SNS.
        Phone number should be in E.164 format (e.g., +1234567890)
        Returns: (success: bool, error_message: str)
        """
        try:
            client = AWSService.get_sns_client()
            client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            logger.info(f"[SMS] Sent to {phone_number}")
            return True, None
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            logger.error(f"[SMS] Failed to send to {phone_number}: {error_msg}")
            return False, error_msg
        except Exception as e:
            logger.error(f"[SMS] Unexpected error for {phone_number}: {str(e)}")
            return False, str(e)

    @staticmethod
    def _send_push(device_token: str, title: str, message: str) -> tuple[bool, str]:
        """
        Send Push notification via AWS SNS.
        Returns: (success: bool, error_message: str)
        """
        try:
            client = AWSService.get_sns_client()

            # Create the push notification payload
            # This works for both APNs (iOS) and FCM (Android)
            payload = json.dumps({
                'default': message,
                'GCM': json.dumps({
                    'notification': {
                        'title': title,
                        'body': message
                    }
                }),
                'APNS': json.dumps({
                    'aps': {
                        'alert': {
                            'title': title,
                            'body': message
                        }
                    }
                }),
                'APNS_SANDBOX': json.dumps({
                    'aps': {
                        'alert': {
                            'title': title,
                            'body': message
                        }
                    }
                })
            })

            # If platform application ARN is configured, send via platform endpoint
            if settings.AWS_SNS_PLATFORM_APPLICATION_ARN:
                # Create or get platform endpoint
                endpoint_response = client.create_platform_endpoint(
                    PlatformApplicationArn=settings.AWS_SNS_PLATFORM_APPLICATION_ARN,
                    Token=device_token
                )
                endpoint_arn = endpoint_response['EndpointArn']

                client.publish(
                    TargetArn=endpoint_arn,
                    Message=payload,
                    MessageStructure='json'
                )
            else:
                # Direct publish to token (for testing)
                client.publish(
                    TargetArn=device_token,
                    Message=payload,
                    MessageStructure='json'
                )

            logger.info(f"[PUSH] Sent to device {device_token[:20]}...")
            return True, None
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            logger.error(f"[PUSH] Failed to send: {error_msg}")
            return False, error_msg
        except Exception as e:
            logger.error(f"[PUSH] Unexpected error: {str(e)}")
            return False, str(e)

    @classmethod
    def send_notification(
        cls,
        channel: str,
        template_name: str,
        parameters: dict,
        recipient: str = None,
        user_id: str = None
    ) -> dict:
        """
        Send notification using template.

        Args:
            channel: Channel type (EMAIL, SMS, PUSH)
            template_name: Name of the template to use
            parameters: Dict of dynamic parameters to replace in template
            recipient: Email, phone number (for EMAIL/SMS)
            user_id: User ID (for PUSH - will look up device tokens)

        Returns:
            Dict with success status and message/log ID
        """
        # Get template
        try:
            template = NotificationTemplate.objects.get(
                name=template_name,
                channel=channel,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return {
                'success': False,
                'error': f"No active template found for '{template_name}' with channel '{channel}'"
            }

        # Render template with parameters
        rendered_subject = render_template(template.subject, parameters)
        rendered_body = render_template(template.body, parameters)

        # Handle different channels
        if channel == ChannelType.EMAIL:
            if not recipient:
                return {'success': False, 'error': 'recipient email is required for EMAIL channel'}
            success, error_msg = cls._send_email(recipient, rendered_subject, rendered_body)
            status = StatusType.SUCCESS if success else StatusType.FAILED

            log = NotificationLog.objects.create(
                template=template,
                channel=channel,
                recipient=recipient,
                subject=rendered_subject,
                message=rendered_body,
                parameters=parameters,
                status=status,
                error_message=error_msg
            )
            return {'success': success, 'log_id': str(log.id), 'error': error_msg}

        elif channel == ChannelType.SMS:
            if not recipient:
                return {'success': False, 'error': 'recipient phone number is required for SMS channel'}
            success, error_msg = cls._send_sms(recipient, rendered_body)
            status = StatusType.SUCCESS if success else StatusType.FAILED

            log = NotificationLog.objects.create(
                template=template,
                channel=channel,
                recipient=recipient,
                message=rendered_body,
                parameters=parameters,
                status=status,
                error_message=error_msg
            )
            return {'success': success, 'log_id': str(log.id), 'error': error_msg}

        elif channel == ChannelType.PUSH:
            device_tokens = []

            if recipient:
                # If device token provided directly
                device_tokens = [recipient]
            elif user_id:
                # Look up device tokens for user
                device_tokens = list(
                    DeviceToken.objects.filter(
                        user_id=user_id,
                        is_active=True
                    ).values_list('device_token', flat=True)
                )
                if not device_tokens:
                    return {'success': False, 'error': f'No active device tokens found for user {user_id}'}
            else:
                return {'success': False, 'error': 'recipient device_token or user_id is required for PUSH channel'}

            results = []
            for token in device_tokens:
                success, error_msg = cls._send_push(token, rendered_subject, rendered_body)
                status = StatusType.SUCCESS if success else StatusType.FAILED

                log = NotificationLog.objects.create(
                    template=template,
                    channel=channel,
                    recipient=token,
                    subject=rendered_subject,
                    message=rendered_body,
                    parameters=parameters,
                    status=status,
                    error_message=error_msg
                )
                results.append({
                    'token': token[:20] + '...',
                    'success': success,
                    'log_id': str(log.id),
                    'error': error_msg
                })

            # Return overall success if at least one succeeded
            any_success = any(r['success'] for r in results)
            return {
                'success': any_success,
                'results': results,
                'total_sent': sum(1 for r in results if r['success']),
                'total_failed': sum(1 for r in results if not r['success'])
            }

        return {'success': False, 'error': f'Unsupported channel: {channel}'}

    @classmethod
    def register_device_token(cls, user_id: str, device_token: str, platform: str) -> dict:
        """
        Register a device token for push notifications.
        """
        try:
            device, created = DeviceToken.objects.update_or_create(
                user_id=user_id,
                device_token=device_token,
                defaults={
                    'platform': platform.upper(),
                    'is_active': True
                }
            )
            return {
                'success': True,
                'created': created,
                'device_id': str(device.id)
            }
        except Exception as e:
            logger.error(f"[PUSH] Failed to register device: {str(e)}")
            return {'success': False, 'error': str(e)}