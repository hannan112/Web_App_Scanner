import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_verification_email(email, token):
    """Send verification email to user"""
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

    # For development, log the URL
    if settings.DEBUG:
        logger.info(f"Verification URL for {email}: {verification_url}")

    # TODO: Implement actual email sending
    # send_mail(
    #     subject='Verify your email',
    #     message=f'Click here to verify your email: {verification_url}',
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[email],
    # )


def send_password_reset_email(email, token):
    """Send password reset email to user"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"

    # For development, log the reset URL
    if settings.DEBUG:
        logger.info(f"Password reset URL for {email}: {reset_url}")

    # TODO: Implement actual email sending
    # send_mail(
    #     subject='Reset your password',
    #     message=f'Click here to reset your password: {reset_url}',
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[email],
    # )
