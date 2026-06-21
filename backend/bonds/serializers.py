"""
Serializers for bond-related API endpoints.

This module contains serializers for:
- Bond master data
- Bond market data
- FX rates
- FX live update requests
- Bond discovery runs
- Bond discovery candidates

Discovery candidates include preview risk/signal fields. These preview fields
are calculated dynamically and are not stored in the database.
"""

from rest_framework import serializers

from bonds.discovery.preview_signal import evaluate_candidate_preview
from bonds.discovery.providers.provider_registry import (
    DEFAULT_DISCOVERY_SOURCE,
    get_supported_provider_names,
)
from bonds.discovery.rating_utils import (
    INVESTMENT_GRADE_MIN_RATING,
    RatingError,
    normalize_rating,
)

from .models import (
    Bond,
    BondCandidate,
    BondMarketData,
    DiscoveryRun,
    FXRate,
)


class BondSerializer(serializers.ModelSerializer):
    """
    Serializer for Bond master data.
    """

    years_to_maturity = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True,
    )
    bond_type_label = serializers.CharField(
        source="get_bond_type_display",
        read_only=True,
    )
    seniority_label = serializers.CharField(
        source="get_seniority_display",
        read_only=True,
    )
    market_liquidity_label = serializers.CharField(
        source="get_market_liquidity_display",
        read_only=True,
    )

    class Meta:
        model = Bond
        fields = [
            "id",
            "name",
            "isin",
            "issuer",
            "bond_type",
            "bond_type_label",
            "currency",
            "seniority",
            "seniority_label",
            "is_callable",
            "market_liquidity",
            "market_liquidity_label",
            "credit_rating",
            "face_value",
            "annual_coupon_rate",
            "coupon_frequency",
            "maturity_date",
            "years_to_maturity",
            "created_at",
            "updated_at",
        ]


class BondMarketDataSerializer(serializers.ModelSerializer):
    """
    Serializer for BondMarketData.
    """

    effective_discount_rate = serializers.DecimalField(
        max_digits=9,
        decimal_places=5,
        read_only=True,
    )
    bond_isin = serializers.CharField(
        source="bond.isin",
        read_only=True,
    )
    bond_name = serializers.CharField(
        source="bond.name",
        read_only=True,
    )

    class Meta:
        model = BondMarketData
        fields = [
            "id",
            "bond",
            "bond_isin",
            "bond_name",
            "quote_date",
            "market_price",
            "market_required_return",
            "ytm",
            "bid_price",
            "ask_price",
            "effective_discount_rate",
            "source",
            "is_manual",
            "notes",
            "created_at",
            "updated_at",
        ]


class FXRateSerializer(serializers.ModelSerializer):
    """
    Serializer for FX rates.
    """

    class Meta:
        model = FXRate
        fields = [
            "id",
            "base_currency",
            "quote_currency",
            "rate_date",
            "rate",
            "source",
            "notes",
            "created_at",
        ]

    def validate(self, attrs):
        """
        Validate and normalize FX rate data.
        """
        base_currency = attrs.get("base_currency", "").upper().strip()
        quote_currency = attrs.get("quote_currency", "").upper().strip()

        if base_currency == quote_currency:
            raise serializers.ValidationError(
                "Base currency and quote currency must be different."
            )

        attrs["base_currency"] = base_currency
        attrs["quote_currency"] = quote_currency

        return attrs


class FXRateUpdateRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting live FX rate updates.

    Expected payload:
        {
            "quote_currency": "EUR",
            "base_currencies": ["USD", "GBP", "CHF", "JPY"]
        }
    """

    quote_currency = serializers.CharField(
        max_length=3,
        default="EUR",
    )
    base_currencies = serializers.ListField(
        child=serializers.CharField(max_length=3),
        required=False,
        allow_empty=False,
    )

    def validate_quote_currency(self, value):
        """
        Normalize quote currency.
        """
        normalized_value = value.upper().strip()

        if len(normalized_value) != 3:
            raise serializers.ValidationError(
                "Quote currency must be a 3-letter currency code."
            )

        return normalized_value

    def validate_base_currencies(self, value):
        """
        Normalize base currencies.
        """
        normalized_currencies = [
            currency.upper().strip()
            for currency in value
            if currency and currency.strip()
        ]

        if not normalized_currencies:
            raise serializers.ValidationError(
                "At least one base currency is required."
            )

        for currency in normalized_currencies:
            if len(currency) != 3:
                raise serializers.ValidationError(
                    "Each base currency must be a 3-letter currency code."
                )

        return normalized_currencies


class DiscoveryRunSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for DiscoveryRun records.
    """

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = DiscoveryRun
        fields = [
            "id",
            "username",
            "source",
            "min_rating",
            "currencies",
            "countries",
            "status",
            "status_label",
            "started_at",
            "finished_at",
            "total_found",
            "total_saved",
            "total_skipped",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BondCandidateSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for discovered bond candidates.

    The preview fields are calculated dynamically and are not database fields.
    They help the frontend show a first-level candidate signal before the bond
    is added to the user's Watchlist.
    """

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )
    discovery_run_id = serializers.IntegerField(
        source="discovery_run.id",
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    preview_risk_level = serializers.SerializerMethodField()
    preview_risk_label = serializers.SerializerMethodField()
    preview_signal = serializers.SerializerMethodField()
    preview_signal_label = serializers.SerializerMethodField()
    preview_reasoning = serializers.SerializerMethodField()

    class Meta:
        model = BondCandidate
        fields = [
            "id",
            "username",
            "discovery_run_id",
            "isin",
            "name",
            "issuer",
            "country",
            "currency",
            "coupon_rate",
            "maturity_date",
            "credit_rating",
            "rating_source",
            "market_price",
            "ytm",
            "duration",
            "source",
            "source_url",
            "ai_summary",
            "ai_reasoning",
            "preview_risk_level",
            "preview_risk_label",
            "preview_signal",
            "preview_signal_label",
            "preview_reasoning",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_preview_risk_level(self, obj):
        """
        Return preview risk level code.
        """
        return self._get_preview(obj).preview_risk_level

    def get_preview_risk_label(self, obj):
        """
        Return preview risk label.
        """
        return self._get_preview(obj).preview_risk_label

    def get_preview_signal(self, obj):
        """
        Return preview signal code.
        """
        return self._get_preview(obj).preview_signal

    def get_preview_signal_label(self, obj):
        """
        Return preview signal label.
        """
        return self._get_preview(obj).preview_signal_label

    def get_preview_reasoning(self, obj):
        """
        Return preview reasoning text.
        """
        return self._get_preview(obj).preview_reasoning

    def _get_preview(self, obj):
        """
        Evaluate and cache preview data for one serializer object.

        SerializerMethodField methods are called separately, so caching avoids
        recalculating the same preview multiple times for the same object.
        """
        if not hasattr(obj, "_cached_candidate_preview"):
            obj._cached_candidate_preview = evaluate_candidate_preview(obj)

        return obj._cached_candidate_preview


class RunBondDiscoverySerializer(serializers.Serializer):
    """
    Serializer for running bond discovery.

    Expected payload:
        {
            "source": "csv_provider",
            "min_rating": "BBB-",
            "currencies": ["EUR", "USD"],
            "countries": ["GR", "US"]
        }

    All fields are optional for the MVP.
    """

    source = serializers.CharField(
        required=False,
        default=DEFAULT_DISCOVERY_SOURCE,
    )
    min_rating = serializers.CharField(
        required=False,
        default=INVESTMENT_GRADE_MIN_RATING,
    )
    currencies = serializers.ListField(
        child=serializers.CharField(max_length=3),
        required=False,
        allow_empty=True,
        default=list,
    )
    countries = serializers.ListField(
        child=serializers.CharField(max_length=2),
        required=False,
        allow_empty=True,
        default=list,
    )

    def validate_source(self, value):
        """
        Validate discovery source.

        Supported sources are defined in the provider registry.
        """
        normalized_value = value.strip().lower()
        supported_sources = get_supported_provider_names()

        if normalized_value not in supported_sources:
            supported_text = ", ".join(supported_sources)

            raise serializers.ValidationError(
                f"Supported discovery sources: {supported_text}."
            )

        return normalized_value

    def validate_min_rating(self, value):
        """
        Normalize and validate the minimum rating.
        """
        try:
            return normalize_rating(value)
        except RatingError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_currencies(self, value):
        """
        Normalize currency filters.
        """
        normalized_currencies = []

        for currency in value:
            if not currency:
                continue

            normalized_currency = currency.upper().strip()

            if len(normalized_currency) != 3:
                raise serializers.ValidationError(
                    "Each currency must be a 3-letter code."
                )

            if normalized_currency not in normalized_currencies:
                normalized_currencies.append(normalized_currency)

        return normalized_currencies

    def validate_countries(self, value):
        """
        Normalize country filters.
        """
        normalized_countries = []

        for country in value:
            if not country:
                continue

            normalized_country = country.upper().strip()

            if len(normalized_country) != 2:
                raise serializers.ValidationError(
                    "Each country must be a 2-letter ISO-style code."
                )

            if normalized_country not in normalized_countries:
                normalized_countries.append(normalized_country)

        return normalized_countries