"""
Django admin configuration for portfolio models.
"""

from django.contrib import admin

from .models import UserBond


@admin.register(UserBond)
class UserBondAdmin(admin.ModelAdmin):
    """
    Admin interface for user Portfolio and Watchlist items.
    """

    list_display = (
        "user",
        "bond",
        "holding_type",
        "quantity",
        "purchase_price",
        "base_currency",
        "is_active",
        "updated_at",
    )
    list_filter = (
        "holding_type",
        "base_currency",
        "is_active",
        "reinvest_coupons",
    )
    search_fields = (
        "user__username",
        "bond__isin",
        "bond__name",
    )
    ordering = (
        "user",
        "holding_type",
        "bond__isin",
    )