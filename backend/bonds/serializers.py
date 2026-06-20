"""
Serializers for bond-related API endpoints.

This module contains serializers for:
- Bond master data
- Bond market data
- FX rates
- FX live update requests
"""

from rest_framework import serializers

from .models import Bond, BondMarketData, FXRate


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