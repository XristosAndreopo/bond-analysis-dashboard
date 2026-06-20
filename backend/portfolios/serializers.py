"""
Serializers for Portfolio and Watchlist API endpoints.
"""

from rest_framework import serializers

from analytics.serializers import BondAnalysisSerializer
from bonds.serializers import BondMarketDataSerializer, BondSerializer
from portfolios.models import UserBond


class UserBondReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for user-owned bond positions.
    """

    bond = BondSerializer(read_only=True)
    holding_type_label = serializers.CharField(
        source="get_holding_type_display",
        read_only=True,
    )
    evaluation_basis_label = serializers.CharField(
        source="get_evaluation_basis_display",
        read_only=True,
    )
    latest_market_data = serializers.SerializerMethodField()
    latest_analysis = serializers.SerializerMethodField()
    position_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=6,
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
            "latest_market_data",
            "latest_analysis",
            "position_value",
            "created_at",
            "updated_at",
        ]

    def get_latest_market_data(self, obj):
        """
        Return latest market data for the position's bond.
        """
        latest_market_data = obj.latest_market_data

        if latest_market_data is None:
            return None

        return BondMarketDataSerializer(latest_market_data).data

    def get_latest_analysis(self, obj):
        """
        Return latest bond analysis for this position.
        """
        latest_analysis = obj.analyses.order_by(
            "-analysis_date",
            "-created_at",
        ).first()

        if latest_analysis is None:
            return None

        return BondAnalysisSerializer(latest_analysis).data


class UserBondWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating and updating Portfolio/Watchlist items.

    The authenticated user is always taken from request.user. The frontend is
    not allowed to assign ownership manually.
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
        extra_kwargs = {
            "holding_type": {"required": False},
        }

    def validate(self, attrs):
        """
        Validate user bond data.

        Rules:
        - request must exist in serializer context.
        - Portfolio positions must have quantity greater than zero.
        - The same active bond cannot exist twice in the same section.
        """
        request = self.context.get("request")

        if request is None:
            raise serializers.ValidationError(
                "Request context is required."
            )

        forced_holding_type = self.context.get("forced_holding_type")
        holding_type = forced_holding_type or attrs.get(
            "holding_type",
            getattr(self.instance, "holding_type", None),
        )

        bond = attrs.get("bond", getattr(self.instance, "bond", None))

        if bond is None:
            raise serializers.ValidationError(
                "Bond is required."
            )

        quantity = attrs.get(
            "quantity",
            getattr(self.instance, "quantity", 0),
        )

        if (
            holding_type == UserBond.HoldingType.PORTFOLIO
            and quantity <= 0
        ):
            raise serializers.ValidationError(
                "Portfolio positions must have quantity greater than zero."
            )

        duplicate_queryset = UserBond.objects.filter(
            user=request.user,
            bond=bond,
            holding_type=holding_type,
            is_active=True,
        )

        if self.instance is not None:
            duplicate_queryset = duplicate_queryset.exclude(
                pk=self.instance.pk,
            )

        if duplicate_queryset.exists():
            raise serializers.ValidationError(
                "This bond already exists in this section for the current user."
            )

        return attrs

    def create(self, validated_data):
        """
        Create a UserBond for request.user.
        """
        request = self.context["request"]
        forced_holding_type = self.context.get("forced_holding_type")

        if forced_holding_type:
            validated_data["holding_type"] = forced_holding_type

        return UserBond.objects.create(
            user=request.user,
            **validated_data,
        )

    def update(self, instance, validated_data):
        """
        Update a UserBond instance.
        """
        forced_holding_type = self.context.get("forced_holding_type")

        if forced_holding_type:
            validated_data["holding_type"] = forced_holding_type

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        return instance


class MoveUserBondSerializer(serializers.Serializer):
    """
    Serializer for moving a position between Portfolio and Watchlist.
    """

    target_holding_type = serializers.ChoiceField(
        choices=UserBond.HoldingType.choices,
    )
    quantity = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    purchase_price = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=14,
        decimal_places=4,
    )

    def validate(self, attrs):
        """
        Validate move request.
        """
        user_bond = self.context.get("user_bond")
        target_holding_type = attrs["target_holding_type"]

        if user_bond is None:
            raise serializers.ValidationError(
                "User bond context is required."
            )

        if user_bond.holding_type == target_holding_type:
            raise serializers.ValidationError(
                "The bond is already in the requested section."
            )

        if (
            target_holding_type == UserBond.HoldingType.PORTFOLIO
            and "quantity" not in attrs
        ):
            raise serializers.ValidationError(
                "Quantity is required when moving to Portfolio."
            )

        return attrs


class PortfolioRowSerializer(serializers.Serializer):
    """
    Serializer for Portfolio table rows.

    Row values are calculated by analytics.portfolio_services.
    """

    user_bond = UserBondReadSerializer()
    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=6,
    )
    weighted_duration = serializers.DecimalField(
        max_digits=20,
        decimal_places=6,
    )
    weighted_risk = serializers.DecimalField(
        max_digits=20,
        decimal_places=6,
    )

    original_position_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=6,
    )
    original_currency = serializers.CharField()
    converted_position_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=6,
        allow_null=True,
    )
    portfolio_base_currency = serializers.CharField()
    fx_rate_to_base = serializers.DecimalField(
        max_digits=18,
        decimal_places=8,
        allow_null=True,
    )
    fx_rate_missing = serializers.BooleanField()
    fx_method = serializers.CharField()