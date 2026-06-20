"""
Serializers for Portfolio and Watchlist items.

These serializers expose a user's own bond positions to the frontend.
The user only sees and manages their own data.
"""

from rest_framework import serializers

from analytics.serializers import BondAnalysisSerializer
from bonds.models import BondMarketData
from bonds.serializers import BondMarketDataSerializer, BondSerializer
from portfolios.models import UserBond


class UserBondReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for Portfolio and Watchlist items.
    """

    bond = BondSerializer(read_only=True)
    latest_market_data = serializers.SerializerMethodField()
    latest_analysis = serializers.SerializerMethodField()
    holding_type_label = serializers.CharField(
        source="get_holding_type_display",
        read_only=True,
    )
    evaluation_basis_label = serializers.CharField(
        source="get_evaluation_basis_display",
        read_only=True,
    )

    class Meta:
        model = UserBond
        fields = [
            "id",
            "bond",
            "holding_type",
            "holding_type_label",
            "quantity",
            "purchase_price",
            "base_currency",
            "reinvest_coupons",
            "trading_fees_percent",
            "coupon_tax_percent",
            "expected_yield_change",
            "valuation_threshold_percent",
            "evaluation_basis",
            "evaluation_basis_label",
            "target_required_return",
            "notes",
            "is_active",
            "position_value",
            "latest_market_data",
            "latest_analysis",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_latest_market_data(self, obj):
        """
        Return latest market data for this bond.
        """
        market_data = obj.latest_market_data

        if market_data is None:
            return None

        return BondMarketDataSerializer(market_data).data

    def get_latest_analysis(self, obj):
        """
        Return latest calculated analysis for this user bond.
        """
        analysis = obj.analyses.order_by(
            "-analysis_date",
            "-created_at",
        ).first()

        if analysis is None:
            return None

        return BondAnalysisSerializer(analysis).data


class UserBondWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating and updating Portfolio/Watchlist items.
    """

    class Meta:
        model = UserBond
        fields = [
            "bond",
            "holding_type",
            "quantity",
            "purchase_price",
            "base_currency",
            "reinvest_coupons",
            "trading_fees_percent",
            "coupon_tax_percent",
            "expected_yield_change",
            "valuation_threshold_percent",
            "evaluation_basis",
            "target_required_return",
            "notes",
            "is_active",
        ]

    def validate(self, attrs):
        """
        Validate ownership and holding rules.
        """
        request = self.context.get("request")
        forced_holding_type = self.context.get("forced_holding_type")

        instance = self.instance

        bond = attrs.get(
            "bond",
            getattr(instance, "bond", None),
        )
        holding_type = (
            forced_holding_type
            or attrs.get("holding_type")
            or getattr(instance, "holding_type", None)
        )
        quantity = attrs.get(
            "quantity",
            getattr(instance, "quantity", 0),
        )

        if request is None:
            raise serializers.ValidationError(
                "Request context is required.",
            )

        if bond is None:
            raise serializers.ValidationError(
                {"bond": "Bond is required."},
            )

        if holding_type == UserBond.HoldingType.PORTFOLIO and quantity <= 0:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        "Portfolio items must have quantity greater than 0."
                    )
                }
            )

        duplicate_queryset = UserBond.objects.filter(
            user=request.user,
            bond=bond,
            holding_type=holding_type,
        )

        if instance is not None:
            duplicate_queryset = duplicate_queryset.exclude(pk=instance.pk)

        if duplicate_queryset.exists():
            raise serializers.ValidationError(
                "This bond already exists in this section for the current user.",
            )

        return attrs

    def create(self, validated_data):
        """
        Create a UserBond for the authenticated user.
        """
        request = self.context["request"]
        forced_holding_type = self.context.get("forced_holding_type")

        if forced_holding_type:
            validated_data["holding_type"] = forced_holding_type

        validated_data["user"] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update a UserBond instance.
        """
        forced_holding_type = self.context.get("forced_holding_type")

        if forced_holding_type:
            validated_data["holding_type"] = forced_holding_type

        return super().update(instance, validated_data)


class MoveUserBondSerializer(serializers.Serializer):
    """
    Serializer for moving a bond between Portfolio and Watchlist.
    """

    target_holding_type = serializers.ChoiceField(
        choices=UserBond.HoldingType.choices,
    )
    quantity = serializers.IntegerField(
        required=False,
        min_value=0,
    )
    purchase_price = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=14,
        decimal_places=4,
    )

    def validate(self, attrs):
        """
        Validate move operation.
        """
        user_bond = self.context["user_bond"]
        target_holding_type = attrs["target_holding_type"]

        if user_bond.holding_type == target_holding_type:
            raise serializers.ValidationError(
                "The bond is already in the selected section.",
            )

        if target_holding_type == UserBond.HoldingType.PORTFOLIO:
            quantity = attrs.get("quantity", user_bond.quantity)

            if quantity <= 0:
                raise serializers.ValidationError(
                    {
                        "quantity": (
                            "Quantity is required when moving a bond "
                            "to Portfolio."
                        )
                    }
                )

        return attrs


class PortfolioRowSerializer(serializers.Serializer):
    """
    Serializer for portfolio table rows with weighted metrics.
    """

    user_bond = UserBondReadSerializer()
    weight = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
    )
    weighted_duration = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
    )
    weighted_risk = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
    )