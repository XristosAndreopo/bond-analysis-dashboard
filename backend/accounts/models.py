"""
Database models for account security workflows.

This module stores temporary security codes for:
- email verification after signup
- password reset requests

Security notes:
- the plain numeric code is never stored in the database
- only a Django password hash of the code is stored
- codes expire automatically based on expires_at
- attempts are counted to limit brute-force guessing
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class AccountSecurityCode(models.Model):
    """
    Temporary hashed code used for account verification and password reset.
    """

    class Purpose(models.TextChoices):
        """
        Supported security-code purposes.
        """

        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", "Email verification"
        PASSWORD_RESET = "PASSWORD_RESET", "Password reset"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_codes",
    )
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=256)
    purpose = models.CharField(
        max_length=32,
        choices=Purpose.choices,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "purpose", "used_at"]),
            models.Index(fields=["user", "purpose", "used_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        """
        Return a readable representation for Django admin/debugging.
        """
        return f"{self.email} - {self.purpose} - {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def is_expired(self):
        """
        Return whether this code is expired.
        """
        return timezone.now() >= self.expires_at

    @property
    def is_used(self):
        """
        Return whether this code has already been used.
        """
        return self.used_at is not None
