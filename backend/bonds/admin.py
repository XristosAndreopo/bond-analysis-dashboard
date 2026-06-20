"""
Django admin configuration for bond-related models.
"""

from django.contrib import admin

from .models import Bond, BondMarketData, FXRate


@admin.register(Bond)
class BondAdmin(admin.ModelAdmin):
    """
    Admin interface for Bond master data.
    """

    list_display = (
        "isin",
        "name",
        "issuer",
        "bond_type",
        "currency",
        "annual_coupon_rate",
        "maturity_date",
        "credit_rating",
        "market_liquidity",
    )
    list_filter = (
        "bond_type",
        "currency",
        "market_liquidity",
        "is_callable",
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
    Admin interface for bond market data.
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
    ordering = (
        "-quote_date",
        "bond__isin",
    )


@admin.register(FXRate)
class FXRateAdmin(admin.ModelAdmin):
    """
    Admin interface for FX rates.
    """

    list_display = (
        "base_currency",
        "quote_currency",
        "rate_date",
        "rate",
        "source",
        "created_at",
    )
    list_filter = (
        "base_currency",
        "quote_currency",
        "rate_date",
        "source",
    )
    search_fields = (
        "base_currency",
        "quote_currency",
        "source",
    )
    ordering = (
        "-rate_date",
        "base_currency",
        "quote_currency",
    )