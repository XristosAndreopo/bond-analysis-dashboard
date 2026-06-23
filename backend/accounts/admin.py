"""
Django admin registration for account security models.
"""

from django.contrib import admin

from .models import AccountSecurityCode


@admin.register(AccountSecurityCode)
class AccountSecurityCodeAdmin(admin.ModelAdmin):
    """
    Read-only oriented admin view for security codes.
    """

    list_display = [
        "email",
        "purpose",
        "expires_at",
        "used_at",
        "attempts",
        "created_at",
    ]
    list_filter = ["purpose", "used_at", "created_at"]
    search_fields = ["email", "user__username"]
    readonly_fields = [
        "user",
        "email",
        "code_hash",
        "purpose",
        "expires_at",
        "used_at",
        "attempts",
        "created_at",
    ]
