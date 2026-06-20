"""
Serializers for bond-related API endpoints.

This module contains serializers for:
- Bond master data
- Bond market data
- FX rates
- FX live update requests
- Bond discovery runs
- Bond discovery candidates

Discovery serializers expose provider-validated candidate data. They do not
trigger AI reasoning and they do not treat AI as a data source.
"""

from rest_framework import serializers

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
    Read serializer for bond discovery runs.

    A discovery run shows one execution of the discovery engine for one user.
    """

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    username = serializers.CharField(
        source="user.username",
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
    Read serializer for discovered bond candidates.

    Candidates are user-specific and become Watchlist items only when the user
    explicitly chooses Add to Watchlist.
    """

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )
    discovery_run_id = serializers.IntegerField(
        source="discovery_run.id",
        read_only=True,
    )

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
            "status",
            "status_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RunBondDiscoverySerializer(serializers.Serializer):
    """
    Serializer for running bond discovery.

    Expected payload:
        {
            "source": "static_provider",
            "min_rating": "BBB-",
            "currencies": ["USD", "EUR"],
            "countries": ["US", "GR"]
        }

    All fields are optional for MVP. If omitted:
        source = static_provider
        min_rating = BBB-
        currencies = []
        countries = []
    """

    source = serializers.CharField(
        max_length=100,
        required=False,
        default="static_provider",
    )
    min_rating = serializers.CharField(
        max_length=20,
        required=False,
        default=INVESTMENT_GRADE_MIN_RATING,
    )
    currencies = serializers.ListField(
        child=serializers.CharField(max_length=3),
        required=False,
        allow_empty=True,
    )
    countries = serializers.ListField(
        child=serializers.CharField(max_length=2),
        required=False,
        allow_empty=True,
    )

    def validate_source(self, value):
        """
        Validate provider source.

        The MVP supports only the static provider. CSV/API providers can be
        added later without changing the frontend contract.
        """
        normalized_value = value.strip()

        if normalized_value != "static_provider":
            raise serializers.ValidationError(
                "Only static_provider is supported in the MVP."
            )

        return normalized_value

    def validate_min_rating(self, value):
        """
        Validate and normalize minimum credit rating.
        """
        try:
            return normalize_rating(value)
        except RatingError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_currencies(self, value):
        """
        Validate and normalize currency filters.
        """
        normalized_currencies = []

        for currency in value:
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
        Validate and normalize country filters.
        """
        normalized_countries = []

        for country in value:
            normalized_country = country.upper().strip()

            if len(normalized_country) != 2:
                raise serializers.ValidationError(
                    "Each country must be a 2-letter code."
                )

            if normalized_country not in normalized_countries:
                normalized_countries.append(normalized_country)

        return normalized_countries