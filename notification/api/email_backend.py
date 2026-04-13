"""
Custom SMTP email backend that injects certifi's CA bundle.
Fixes SSL certificate verification on macOS and minimal Linux environments.
"""
import ssl
import certifi
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend


class EmailBackend(DjangoSMTPBackend):
    """SMTP backend using certifi's trusted CA bundle for SSL/TLS."""

    def open(self):
        if self.connection:
            return False

        connection_params = {'local_hostname': None}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout

        ssl_context = ssl.create_default_context(cafile=certifi.where())

        if self.use_ssl:
            connection_params['context'] = ssl_context

        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                self.connection.starttls(context=ssl_context)
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except OSError:
            if not self.fail_silently:
                raise
        return False
