"""
Bond domain models.

This module contains:
- Bond master data
- Bond market data
- FX rates used for portfolio currency conversion

FX conversion is intentionally manual for the MVP. Later, FX rates can be
loaded automatically from an external data provider.
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Bond(models.Model):
    """
    Bond master data.

    Bonds are shared master records. User-specific ownership information lives
    in the UserBond model inside the portfolios app.
    """

    class BondType(models.TextChoices):
        GOVERNMENT = "GOVERNMENT", "Government Bond"
        CORPORATE = "CORPORATE", "Corporate Bond"
        TREASURY = "TREASURY", "Treasury"
        MUNICIPAL = "MUNICIPAL", "Municipal Bond"
        OTHER = "OTHER", "Other"

    class Seniority(models.TextChoices):
        SENIOR_SECURED = "SENIOR_SECURED", "Senior Secured"
        SENIOR_UNSECURED = "SENIOR_UNSECURED", "Senior Unsecured"
        SUBORDINATED = "SUBORDINATED", "Subordinated"
        JUNIOR = "JUNIOR", "Junior"
        OTHER = "OTHER", "Other"

    class MarketLiquidity(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    name = models.CharField(max_length=255)
    isin = models.CharField(max_length=20, unique=True, db_index=True)
    issuer = models.CharField(max_length=255)
    bond_type = models.CharField(
        max_length=30,
        choices=BondType.choices,
        default=BondType.GOVERNMENT,
    )
    currency = models.CharField(max_length=3, default="EUR")
    seniority = models.CharField(
        max_length=30,
        choices=Seniority.choices,
        default=Seniority.SENIOR_UNSECURED,
    )
    is_callable = models.BooleanField(default=False)
    market_liquidity = models.CharField(
        max_length=20,
        choices=MarketLiquidity.choices,
        default=MarketLiquidity.MEDIUM,
    )
    credit_rating = models.CharField(max_length=20, blank=True)
    face_value = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("100.0000"),
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    annual_coupon_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("100.0000")),
        ],
        help_text="Annual coupon rate as percentage. Example: 4.125 means 4.125%.",
    )
    coupon_frequency = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Number of coupon payments per year.",
    )
    maturity_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["isin"]

    def __str__(self):
        """
        Return human-readable representation.
        """
        return f"{self.isin} - {self.name}"

    @property
    def years_to_maturity(self):
        """
        Calculate approximate years to maturity from today.

        Returns:
            Decimal years to maturity rounded to 2 decimals.
        """
        today = timezone.localdate()

        if self.maturity_date <= today:
            return Decimal("0.00")

        days_to_maturity = (self.maturity_date - today).days
        years = Decimal(days_to_maturity) / Decimal("365.25")

        return years.quantize(Decimal("0.01"))


class BondMarketData(models.Model):
    """
    Market data for a bond.

    The market_required_return field is the primary discount rate used by the
    analysis engine. If it is missing, ytm is used as fallback.
    """

    bond = models.ForeignKey(
        Bond,
        on_delete=models.CASCADE,
        related_name="market_data",
    )
    quote_date = models.DateField(default=timezone.localdate, db_index=True)
    market_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0000"))],
    )
    market_required_return = models.DecimalField(
        max_digits=9,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="Market required return as percentage. Example: 4.35 means 4.35%.",
    )
    ytm = models.DecimalField(
        max_digits=9,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="Yield to maturity as percentage. Used as fallback discount rate.",
    )
    bid_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
    )
    ask_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
    )
    source = models.CharField(max_length=100, default="manual")
    is_manual = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-quote_date", "-created_at"]
        unique_together = ("bond", "quote_date", "source")

    def __str__(self):
        """
        Return human-readable representation.
        """
        return f"{self.bond.isin} - {self.quote_date} - {self.market_price}"

    @property
    def effective_discount_rate(self):
        """
        Return the effective discount rate used by analysis.

        Priority:
            1. market_required_return
            2. ytm
            3. None
        """
        if self.market_required_return is not None:
            return self.market_required_return

        if self.ytm is not None:
            return self.ytm

        return None


class FXRate(models.Model):
    """
    Manual FX rate used for portfolio currency conversion.

    Example:
        base_currency = USD
        quote_currency = EUR
        rate = 0.920000

    Meaning:
        1 USD = 0.92 EUR

    This allows the portfolio to convert USD bond values into EUR.
    """

    base_currency = models.CharField(
        max_length=3,
        help_text="Currency being converted from. Example: USD.",
    )
    quote_currency = models.CharField(
        max_length=3,
        help_text="Currency being converted to. Example: EUR.",
    )
    rate_date = models.DateField(default=timezone.localdate, db_index=True)
    rate = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        validators=[MinValueValidator(Decimal("0.00000001"))],
        help_text="Conversion rate. Example: 1 USD = 0.92 EUR, rate = 0.92.",
    )
    source = models.CharField(max_length=100, default="manual")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-rate_date", "base_currency", "quote_currency"]
        unique_together = (
            "base_currency",
            "quote_currency",
            "rate_date",
            "source",
        )

    def __str__(self):
        """
        Return human-readable representation.
        """
        return (
            f"1 {self.base_currency.upper()} = "
            f"{self.rate} {self.quote_currency.upper()} "
            f"({self.rate_date})"
        )

    def save(self, *args, **kwargs):
        """
        Normalize currency codes before saving.
        """
        self.base_currency = self.base_currency.upper()
        self.quote_currency = self.quote_currency.upper()

        super().save(*args, **kwargs)