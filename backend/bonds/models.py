"""
Bond domain models.

This module contains:
- Bond master data
- Bond market data
- FX rates used for portfolio currency conversion
- Bond discovery run records
- Bond discovery candidate records

FX conversion is intentionally manual for the MVP. Later, FX rates can be
loaded automatically from an external data provider.

The discovery models do not use AI as a data source. They only store validated
candidate data coming from a provider such as a static provider, CSV import, or
future external API.
"""

from decimal import Decimal

from django.conf import settings
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


class DiscoveryRun(models.Model):
    """
    Stores one bond discovery execution for one user.

    A discovery run records:
    - who started the discovery
    - which provider/source was used
    - what filters were applied
    - how many candidates were found, saved, or skipped

    The run does not perform analysis by itself. It only tracks the discovery
    process that creates BondCandidate records.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bond_discovery_runs",
    )
    source = models.CharField(
        max_length=100,
        default="static_provider",
        help_text="Discovery provider name, for example static_provider or csv_provider.",
    )
    min_rating = models.CharField(
        max_length=20,
        default="BBB-",
        help_text="Minimum accepted credit rating for this run.",
    )
    currencies = models.JSONField(
        default=list,
        blank=True,
        help_text="Optional currency filters used by the discovery run.",
    )
    countries = models.JSONField(
        default=list,
        blank=True,
        help_text="Optional country filters used by the discovery run.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(
        default=timezone.now,
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    total_found = models.PositiveIntegerField(
        default=0,
        help_text="Raw candidates returned by the provider.",
    )
    total_saved = models.PositiveIntegerField(
        default=0,
        help_text="Candidates saved after validation and filtering.",
    )
    total_skipped = models.PositiveIntegerField(
        default=0,
        help_text="Candidates skipped due to validation, filtering, or duplicates.",
    )
    error_message = models.TextField(
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-started_at", "-created_at"]
        verbose_name = "Discovery Run"
        verbose_name_plural = "Discovery Runs"

    def __str__(self):
        """
        Return a readable representation of the discovery run.
        """
        return (
            f"{self.user} - {self.source} - "
            f"{self.status} - {self.started_at:%Y-%m-%d %H:%M}"
        )

    def mark_running(self):
        """
        Mark the discovery run as running.
        """
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.error_message = ""
        self.save(
            update_fields=[
                "status",
                "started_at",
                "error_message",
                "updated_at",
            ]
        )

    def mark_completed(self, total_found, total_saved, total_skipped):
        """
        Mark the discovery run as completed and store run totals.

        Args:
            total_found: Number of raw provider candidates.
            total_saved: Number of saved candidates.
            total_skipped: Number of skipped candidates.
        """
        self.status = self.Status.COMPLETED
        self.finished_at = timezone.now()
        self.total_found = total_found
        self.total_saved = total_saved
        self.total_skipped = total_skipped
        self.error_message = ""
        self.save(
            update_fields=[
                "status",
                "finished_at",
                "total_found",
                "total_saved",
                "total_skipped",
                "error_message",
                "updated_at",
            ]
        )

    def mark_failed(self, error_message):
        """
        Mark the discovery run as failed.

        Args:
            error_message: Human-readable error message.
        """
        self.status = self.Status.FAILED
        self.finished_at = timezone.now()
        self.error_message = str(error_message)
        self.save(
            update_fields=[
                "status",
                "finished_at",
                "error_message",
                "updated_at",
            ]
        )


class BondCandidate(models.Model):
    """
    Stores one discovered bond candidate for review.

    A candidate is not automatically a Bond master record. It becomes part of
    the user's Watchlist only after the user explicitly chooses Add to Watchlist.

    Candidates are user-specific because each user has a separate Watchlist and
    Portfolio.
    """

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        REVIEWED = "REVIEWED", "Reviewed"
        ADDED_TO_WATCHLIST = "ADDED_TO_WATCHLIST", "Added to Watchlist"
        IGNORED = "IGNORED", "Ignored"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bond_candidates",
    )
    discovery_run = models.ForeignKey(
        DiscoveryRun,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    isin = models.CharField(
        max_length=20,
        db_index=True,
        help_text="International Securities Identification Number.",
    )
    name = models.CharField(
        max_length=255,
    )
    issuer = models.CharField(
        max_length=255,
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        help_text="Issuer country code, for example US or GR.",
    )
    currency = models.CharField(
        max_length=3,
        default="EUR",
    )
    coupon_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("100.0000")),
        ],
        help_text="Annual coupon rate as percentage. Example: 4.125 means 4.125%.",
    )
    maturity_date = models.DateField(
        db_index=True,
    )
    credit_rating = models.CharField(
        max_length=20,
        db_index=True,
    )
    rating_source = models.CharField(
        max_length=100,
        blank=True,
    )
    market_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0000"))],
    )
    ytm = models.DecimalField(
        max_digits=9,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("-100.00000")),
            MaxValueValidator(Decimal("100.00000")),
        ],
        help_text="Yield to maturity as percentage.",
    )
    duration = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.000000"))],
        help_text="Modified or approximate duration if provided by the source.",
    )
    source = models.CharField(
        max_length=100,
        default="static_provider",
    )
    source_url = models.URLField(
        max_length=500,
        blank=True,
    )
    ai_summary = models.TextField(
        blank=True,
        help_text="Optional future AI-generated summary based only on validated data.",
    )
    ai_reasoning = models.TextField(
        blank=True,
        help_text="Optional future AI-generated reasoning based only on validated data.",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["maturity_date", "isin"]
        verbose_name = "Bond Candidate"
        verbose_name_plural = "Bond Candidates"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "isin"],
                name="unique_bond_candidate_per_user_isin",
            ),
        ]

    def __str__(self):
        """
        Return a readable representation of the bond candidate.
        """
        return f"{self.user} - {self.isin} - {self.status}"

    def save(self, *args, **kwargs):
        """
        Normalize key text fields before saving.
        """
        self.isin = self.isin.upper().strip()
        self.currency = self.currency.upper().strip()

        if self.country:
            self.country = self.country.upper().strip()

        if self.credit_rating:
            self.credit_rating = self.credit_rating.upper().strip()

        super().save(*args, **kwargs)