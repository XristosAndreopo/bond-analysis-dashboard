"""
Serializers for bond-related API endpoints.
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
        Validate FX rate data.
        """
        base_currency = attrs.get("base_currency", "").upper()
        quote_currency = attrs.get("quote_currency", "").upper()

        if base_currency == quote_currency:
            raise serializers.ValidationError(
                "Base currency and quote currency must be different."
            )

        attrs["base_currency"] = base_currency
        attrs["quote_currency"] = quote_currency

        return attrs