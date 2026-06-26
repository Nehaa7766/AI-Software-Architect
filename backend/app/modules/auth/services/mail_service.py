"""Transactional email (verification + password reset) via fastapi-mail.

In development MAIL_SUPPRESS_SEND is true: messages are not actually sent, and
the reset/verify links are logged so you can test the flow without an SMTP server.
"""
import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

logger = logging.getLogger("auth.mail")

_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=1 if settings.MAIL_SUPPRESS_SEND else 0,
)


class MailService:
    def __init__(self) -> None:
        self._mailer = FastMail(_conf)

    async def _send(self, *, to: str, subject: str, html: str) -> None:
        message = MessageSchema(
            subject=subject, recipients=[to], body=html, subtype=MessageType.html
        )
        await self._mailer.send_message(message)

    async def send_password_reset(self, *, to: str, reset_link: str) -> None:
        if settings.MAIL_SUPPRESS_SEND:
            logger.info("[DEV] Password reset link for %s: %s", to, reset_link)
        html = (
            f"<p>You requested a password reset.</p>"
            f'<p><a href="{reset_link}">Reset your password</a></p>'
            f"<p>This link expires in {settings.RESET_TOKEN_TTL_MINUTES} minutes. "
            f"If you did not request this, ignore this email.</p>"
        )
        await self._send(to=to, subject="Reset your password", html=html)

    async def send_verification(self, *, to: str, verify_link: str) -> None:
        if settings.MAIL_SUPPRESS_SEND:
            logger.info("[DEV] Email verification link for %s: %s", to, verify_link)
        html = (
            f"<p>Welcome to AI Software Architect!</p>"
            f'<p><a href="{verify_link}">Verify your email</a></p>'
            f"<p>This link expires in {settings.VERIFY_TOKEN_TTL_HOURS} hours.</p>"
        )
        await self._send(to=to, subject="Verify your email", html=html)


mail_service = MailService()
