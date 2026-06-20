"""
Serializers for bond analysis results.

These serializers expose calculated analysis data and cash flows to the
React frontend. Analysis records are read-only from the API because they are
calculated automatically by backend services.
"""

from rest_framework import serializers

from .models import BondAnalysis, CashFlow


class CashFlowSerializer(serializers.ModelSerializer):
    """
    Serializer for calculated cash flow rows.
    """

    class Meta:
        model = CashFlow
        fields = [
            "id",
            "period_number",
            "payment_date",
            "coupon_gross",
            "coupon_tax",
            "coupon_net",
            "principal",
            "total_cash_flow",
            "discounted_cash_flow",
        ]
        read_only_fields = fields


class BondAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer for calculated bond analysis results.

    The serializer includes display labels for risk level and final signal so
    the frontend can show user-friendly Greek signal text.
    """

    risk_level_label = serializers.CharField(
        source="get_risk_level_display",
        read_only=True,
    )
    final_signal_label = serializers.CharField(
        source="get_final_signal_display",
        read_only=True,
    )
    cash_flows = CashFlowSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = BondAnalysis
        fields = [
            "id",
            "analysis_date",
            "intrinsic_value",
            "iv_to_cost",
            "iv_vs_market_price",
            "market_price_minus_face_value",
            "current_yield",
            "net_ytm",
            "approx_aytm",
            "rcy",
            "macaulay_duration",
            "modified_duration",
            "price_impact",
            "estimated_price",
            "risk_score",
            "risk_level",
            "risk_level_label",
            "position_value",
            "final_signal",
            "final_signal_label",
            "reasoning",
            "risk_reasoning",
            "calculation_notes",
            "cash_flows",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields