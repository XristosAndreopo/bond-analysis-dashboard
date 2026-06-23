"""
Services for account email verification and password reset codes.

The service functions keep security logic outside API views:
- code generation
- code hashing and validation
- expiration checks
- attempt counting
- email sending
"""

from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import AccountSecurityCode


DEFAULT_CODE_LENGTH = 6
DEFAULT_CODE_EXPIRY_MINUTES = 15
DEFAULT_CODE_MAX_ATTEMPTS = 5


class AccountSecurityCodeError(Exception):
    """
    Raised when a security code is invalid, expired, or locked.
    """


def get_code_expiry_minutes():
    """
    Return configured security-code expiry time in minutes.
    """
    return int(
        getattr(
            settings,
            "ACCOUNT_SECURITY_CODE_EXPIRY_MINUTES",
            DEFAULT_CODE_EXPIRY_MINUTES,
        )
    )


def get_code_max_attempts():
    """
    Return configured maximum validation attempts per code.
    """
    return int(
        getattr(
            settings,
            "ACCOUNT_SECURITY_CODE_MAX_ATTEMPTS",
            DEFAULT_CODE_MAX_ATTEMPTS,
        )
    )


def generate_numeric_code(length=DEFAULT_CODE_LENGTH):
    """
    Generate a cryptographically secure numeric code.

    Args:
        length: Number of digits.

    Returns:
        str: Numeric code.
    """
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


@transaction.atomic
def create_security_code(user, purpose):
    """
    Create a new security code and invalidate older active codes.

    Args:
        user: Django User instance.
        purpose: AccountSecurityCode.Purpose value.

    Returns:
        tuple[AccountSecurityCode, str]: Created code row and plain code.
    """
    now = timezone.now()

    AccountSecurityCode.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).update(used_at=now)

    plain_code = generate_numeric_code()

    security_code = AccountSecurityCode.objects.create(
        user=user,
        email=user.email,
        purpose=purpose,
        code_hash=make_password(plain_code),
        expires_at=now + timedelta(minutes=get_code_expiry_minutes()),
    )

    return security_code, plain_code


def send_email_verification_code(user):
    """
    Create and send an email verification code.

    Args:
        user: Django User instance.

    Returns:
        AccountSecurityCode: Created code row.
    """
    security_code, plain_code = create_security_code(
        user=user,
        purpose=AccountSecurityCode.Purpose.EMAIL_VERIFICATION,
    )

    send_mail(
        subject="Verify your Bond Analysis Dashboard account",
        message=(
            "Welcome to Bond Analysis Dashboard.\n\n"
            f"Your verification code is: {plain_code}\n\n"
            f"This code expires in {get_code_expiry_minutes()} minutes.\n"
            "If you did not create this account, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return security_code


def send_password_reset_code(user):
    """
    Create and send a password reset code.

    Args:
        user: Django User instance.

    Returns:
        AccountSecurityCode: Created code row.
    """
    security_code, plain_code = create_security_code(
        user=user,
        purpose=AccountSecurityCode.Purpose.PASSWORD_RESET,
    )

    send_mail(
        subject="Reset your Bond Analysis Dashboard password",
        message=(
            "You requested a password reset for Bond Analysis Dashboard.\n\n"
            f"Your temporary password reset code is: {plain_code}\n\n"
            f"This code expires in {get_code_expiry_minutes()} minutes.\n"
            "If you did not request this, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return security_code


@transaction.atomic
def validate_security_code(email, plain_code, purpose):
    """
    Validate a submitted security code.

    Args:
        email: User email address.
        plain_code: Submitted numeric code.
        purpose: AccountSecurityCode.Purpose value.

    Returns:
        User: User connected to the valid code.

    Raises:
        AccountSecurityCodeError: If validation fails.
    """
    normalized_email = email.strip().lower()
    submitted_code = str(plain_code).strip()

    security_code = (
        AccountSecurityCode.objects.select_for_update()
        .select_related("user")
        .filter(
            email__iexact=normalized_email,
            purpose=purpose,
            used_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )

    if security_code is None:
        raise AccountSecurityCodeError("Invalid or expired code.")

    if security_code.is_expired:
        security_code.used_at = timezone.now()
        security_code.save(update_fields=["used_at"])
        raise AccountSecurityCodeError("Invalid or expired code.")

    if security_code.attempts >= get_code_max_attempts():
        security_code.used_at = timezone.now()
        security_code.save(update_fields=["used_at"])
        raise AccountSecurityCodeError("Too many attempts. Request a new code.")

    security_code.attempts += 1
    security_code.save(update_fields=["attempts"])

    if not check_password(submitted_code, security_code.code_hash):
        raise AccountSecurityCodeError("Invalid or expired code.")

    security_code.used_at = timezone.now()
    security_code.save(update_fields=["used_at"])

    return security_code.user
