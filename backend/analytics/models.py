"""
Database models for bond analysis results and cash flows.

The analysis records are calculated automatically by backend services. The
user should not manually create or trigger analysis from the frontend.
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from bonds.models import BondMarketData
from portfolios.models import UserBond


class BondAnalysis(models.Model):
    """
    Stores calculated analysis results for a UserBond.

    There should be at most one analysis per UserBond and analysis_date.
    The calculation service uses update_or_create to avoid duplicate rows
    for the same user bond and date.
    """

    class RiskLevel(models.TextChoices):
        VERY_LOW = "VERY_LOW", "Very Low"
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        VERY_HIGH = "VERY_HIGH", "Very High"

    class Signal(models.TextChoices):
        BUY = "BUY", "Αγορά"
        BUY_WITH_CAUTION = "BUY_WITH_CAUTION", "Αγορά με προσοχή"
        BUY_LOW_YIELD = "BUY_LOW_YIELD", "Αγορά αλλά με χαμηλή απόδοση"
        DO_NOT_BUY_WAIT = "DO_NOT_BUY_WAIT", "Μη αγορά / Περίμενε"
        HOLD = "HOLD", "Διακράτηση"
        SELL = "SELL", "Πώληση"
        PARTIAL_SELL = "PARTIAL_SELL", "Μερική πώληση"
        BUY_MORE = "BUY_MORE", "Αγορά επιπλέον"
        REVIEW = "REVIEW", "Επανεξέταση"

    user_bond = models.ForeignKey(
        UserBond,
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    analysis_date = models.DateField(
        default=timezone.localdate,
        db_index=True,
    )
    market_data = models.ForeignKey(
        BondMarketData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyses",
    )

    intrinsic_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    iv_to_cost = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Intrinsic value divided by cost.",
    )
    iv_vs_market_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Intrinsic value minus market price.",
    )
    market_price_minus_face_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    current_yield = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
    )
    net_ytm = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
    )
    approx_aytm = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Approximate annual yield to maturity.",
    )
    rcy = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Reinvested coupon yield.",
    )
    macaulay_duration = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
    )
    modified_duration = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
    )
    price_impact = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Estimated price impact based on expected yield change.",
    )
    estimated_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    risk_score = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("100.0000")),
        ],
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
    )
    position_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )
    final_signal = models.CharField(
        max_length=30,
        choices=Signal.choices,
        default=Signal.REVIEW,
    )
    reasoning = models.TextField(
        blank=True,
        help_text="Short explanation for the final analytical signal.",
    )
    risk_reasoning = models.TextField(
        blank=True,
        help_text="Short explanation for the risk level.",
    )
    calculation_notes = models.TextField(
        blank=True,
        help_text="Internal notes about missing data or calculation limits.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-analysis_date", "-created_at"]
        unique_together = ("user_bond", "analysis_date")
        verbose_name = "Bond Analysis"
        verbose_name_plural = "Bond Analyses"

    def __str__(self):
        """Return a readable representation of the analysis record."""
        return (
            f"{self.user_bond.user.username} - "
            f"{self.user_bond.bond.isin} - "
            f"{self.analysis_date}"
        )


class CashFlow(models.Model):
    """
    Stores calculated cash flow rows for a BondAnalysis.

    Cash flows are generated by the analysis service and displayed on the
    Bond Detail page.
    """

    analysis = models.ForeignKey(
        BondAnalysis,
        on_delete=models.CASCADE,
        related_name="cash_flows",
    )
    period_number = models.PositiveIntegerField()
    payment_date = models.DateField()
    coupon_gross = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )
    coupon_tax = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )
    coupon_net = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )
    principal = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )
    total_cash_flow = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )
    discounted_cash_flow = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0.000000"),
    )

    class Meta:
        ordering = ["period_number"]
        unique_together = ("analysis", "period_number")
        verbose_name = "Cash Flow"
        verbose_name_plural = "Cash Flows"

    def __str__(self):
        """Return a readable representation of the cash flow row."""
        return (
            f"{self.analysis.user_bond.bond.isin} - "
            f"Period {self.period_number}"
        )