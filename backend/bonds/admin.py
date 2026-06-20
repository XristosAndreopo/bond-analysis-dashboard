"""
Django admin configuration for bond models.
"""

from django.contrib import admin

from .models import Bond, BondMarketData


@admin.register(Bond)
class BondAdmin(admin.ModelAdmin):
    """
    Admin interface for Bond records.
    """

    list_display = (
        "isin",
        "name",
        "issuer",
        "bond_type",
        "currency",
        "credit_rating",
        "maturity_date",
        "years_to_maturity",
    )
    list_filter = (
        "bond_type",
        "currency",
        "seniority",
        "is_callable",
        "market_liquidity",
    )
    search_fields = (
        "isin",
        "name",
        "issuer",
        "credit_rating",
    )
    ordering = ("isin",)


@admin.register(BondMarketData)
class BondMarketDataAdmin(admin.ModelAdmin):
    """
    Admin interface for BondMarketData records.
    """

    list_display = (
        "bond",
        "quote_date",
        "market_price",
        "market_required_return",
        "ytm",
        "source",
        "is_manual",
    )
    list_filter = (
        "quote_date",
        "source",
        "is_manual",
    )
    search_fields = (
        "bond__isin",
        "bond__name",
        "source",
    )
    ordering = ("-quote_date", "-created_at")