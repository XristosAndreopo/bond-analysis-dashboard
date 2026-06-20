"""
Database models for user bond holdings.

This module connects Django users with bonds. A user can keep a bond either
in the Portfolio, meaning it has been bought, or in the Watchlist, meaning it
is only being monitored.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from bonds.models import Bond


class UserBond(models.Model):
    """
    Represents a user's relationship with a bond.

    A UserBond may belong to:
    - Portfolio: the user owns the bond.
    - Watchlist: the user monitors the bond but does not own it.

    The analysis engine will calculate results based on this model and the
    latest available BondMarketData.
    """

    class HoldingType(models.TextChoices):
        PORTFOLIO = "PORTFOLIO", "Portfolio"
        WATCHLIST = "WATCHLIST", "Watchlist"

    class EvaluationBasis(models.TextChoices):
        MARKET_DATA = "MARKET_DATA", "Market Data"
        PERSONAL_TARGET = "PERSONAL_TARGET", "Personal Target"
        CONSERVATIVE = "CONSERVATIVE", "Conservative"
        BALANCED = "BALANCED", "Balanced"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_bonds",
    )
    bond = models.ForeignKey(
        Bond,
        on_delete=models.CASCADE,
        related_name="user_positions",
    )
    holding_type = models.CharField(
        max_length=20,
        choices=HoldingType.choices,
        default=HoldingType.WATCHLIST,
    )
    quantity = models.PositiveIntegerField(
        default=0,
        help_text="Number of bonds owned. Usually 0 for Watchlist items.",
    )
    purchase_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0000"))],
        help_text="Purchase price per bond, if the bond is in Portfolio.",
    )
    base_currency = models.CharField(
        max_length=3,
        default="EUR",
        help_text="Investor base currency, for example EUR or USD.",
    )
    reinvest_coupons = models.BooleanField(
        default=False,
        help_text="Used for reinvested coupon yield calculations.",
    )
    trading_fees_percent = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("100.0000")),
        ],
        help_text="Trading fees as percentage.",
    )
    coupon_tax_percent = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("100.0000")),
        ],
        help_text="Coupon tax as percentage.",
    )
    expected_yield_change = models.DecimalField(
        max_digits=9,
        decimal_places=5,
        default=Decimal("0.00000"),
        validators=[
            MinValueValidator(Decimal("-100.00000")),
            MaxValueValidator(Decimal("100.00000")),
        ],
        help_text="Expected yield change Δy as percentage.",
    )
    valuation_threshold_percent = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("100.0000")),
        ],
        help_text="Threshold used to decide if IV is materially above/below MP.",
    )
    evaluation_basis = models.CharField(
        max_length=30,
        choices=EvaluationBasis.choices,
        default=EvaluationBasis.MARKET_DATA,
    )
    target_required_return = models.DecimalField(
        max_digits=9,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("-100.00000")),
            MaxValueValidator(Decimal("100.00000")),
        ],
        help_text=(
            "Optional personal return target. This is not the main market "
            "discount rate used for valuation."
        ),
    )
    notes = models.TextField(
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["user", "holding_type", "bond__isin"]
        unique_together = ("user", "bond", "holding_type")
        verbose_name = "User Bond"
        verbose_name_plural = "User Bonds"

    def __str__(self):
        """Return a readable representation of the user bond item."""
        return f"{self.user.username} - {self.bond.isin} - {self.holding_type}"

    @property
    def latest_market_data(self):
        """
        Return the latest market data for this bond.

        The frontend should always display analysis based on the latest
        available market data.
        """
        return self.bond.market_data.order_by("-quote_date", "-created_at").first()

    @property
    def position_value(self):
        """
        Calculate the current position value.

        For Portfolio items:
        quantity × latest market price.

        For Watchlist items:
        0, because the user does not own the bond.
        """
        if self.holding_type != self.HoldingType.PORTFOLIO:
            return Decimal("0.0000")

        latest_data = self.latest_market_data

        if latest_data is not None:
            price = latest_data.market_price
        elif self.purchase_price is not None:
            price = self.purchase_price
        else:
            price = self.bond.face_value

        return Decimal(self.quantity) * price