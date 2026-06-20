"""
Django admin configuration for bond-related models.

This module registers:
- Bond master data
- Bond market data
- FX rates
- Discovery runs
- Bond candidates

The discovery admin screens are useful for reviewing what the discovery engine
found, saved, skipped, or marked as added/ignored.
"""

from django.contrib import admin

from .models import (
    Bond,
    BondCandidate,
    BondMarketData,
    DiscoveryRun,
    FXRate,
)


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


@admin.register(DiscoveryRun)
class DiscoveryRunAdmin(admin.ModelAdmin):
    """
    Admin interface for bond discovery run records.

    A discovery run shows one execution of the discovery engine for one user.
    """

    list_display = (
        "id",
        "user",
        "source",
        "min_rating",
        "status",
        "started_at",
        "finished_at",
        "total_found",
        "total_saved",
        "total_skipped",
    )
    list_filter = (
        "status",
        "source",
        "min_rating",
        "started_at",
        "finished_at",
    )
    search_fields = (
        "user__username",
        "source",
        "min_rating",
        "error_message",
    )
    readonly_fields = (
        "started_at",
        "finished_at",
        "created_at",
        "updated_at",
    )
    ordering = (
        "-started_at",
        "-created_at",
    )


@admin.register(BondCandidate)
class BondCandidateAdmin(admin.ModelAdmin):
    """
    Admin interface for discovered bond candidates.

    Candidates are user-specific and become Watchlist items only when the user
    explicitly adds them to My Watchlist.
    """

    list_display = (
        "isin",
        "name",
        "issuer",
        "user",
        "country",
        "currency",
        "credit_rating",
        "maturity_date",
        "market_price",
        "ytm",
        "duration",
        "status",
        "source",
        "created_at",
    )
    list_filter = (
        "status",
        "source",
        "currency",
        "country",
        "credit_rating",
        "maturity_date",
        "created_at",
    )
    search_fields = (
        "isin",
        "name",
        "issuer",
        "user__username",
        "credit_rating",
        "rating_source",
        "source",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = (
        "maturity_date",
        "isin",
    )