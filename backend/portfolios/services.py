"""
Portfolio service functions.

This module contains portfolio-level calculations used by the API. Keeping
these calculations in a service layer keeps views and serializers clean.
"""

from decimal import Decimal, ROUND_HALF_UP

from analytics.models import BondAnalysis
from portfolios.models import UserBond


ZERO = Decimal("0")


def quantize_decimal(value, places="0.000001"):
    """
    Quantize Decimal values for stable API output.

    Args:
        value: Decimal value.
        places: Decimal precision pattern.

    Returns:
        Decimal.
    """
    return Decimal(value).quantize(
        Decimal(places),
        rounding=ROUND_HALF_UP,
    )


def get_latest_analysis(user_bond):
    """
    Return the latest analysis for a user bond.
    """
    return user_bond.analyses.order_by(
        "-analysis_date",
        "-created_at",
    ).first()


def get_portfolio_risk_level(portfolio_risk_score):
    """
    Convert a portfolio risk score into a risk level.

    This mirrors the risk levels used for individual bond analysis.
    """
    if portfolio_risk_score <= Decimal("20"):
        return BondAnalysis.RiskLevel.VERY_LOW

    if portfolio_risk_score <= Decimal("35"):
        return BondAnalysis.RiskLevel.LOW

    if portfolio_risk_score <= Decimal("55"):
        return BondAnalysis.RiskLevel.MEDIUM

    if portfolio_risk_score <= Decimal("75"):
        return BondAnalysis.RiskLevel.HIGH

    return BondAnalysis.RiskLevel.VERY_HIGH


def get_portfolio_risk_level_label(portfolio_risk_level):
    """
    Return a user-friendly risk level label.
    """
    labels = {
        BondAnalysis.RiskLevel.VERY_LOW: "Very Low",
        BondAnalysis.RiskLevel.LOW: "Low",
        BondAnalysis.RiskLevel.MEDIUM: "Medium",
        BondAnalysis.RiskLevel.HIGH: "High",
        BondAnalysis.RiskLevel.VERY_HIGH: "Very High",
    }

    return labels.get(portfolio_risk_level, "Medium")


def calculate_portfolio_summary(user):
    """
    Calculate portfolio-level metrics for a user.

    Metrics:
    - total portfolio value
    - portfolio duration
    - portfolio risk score
    - portfolio risk level
    - number of bonds
    - signal counts
    """
    user_bonds = UserBond.objects.filter(
        user=user,
        holding_type=UserBond.HoldingType.PORTFOLIO,
        is_active=True,
    ).select_related(
        "bond",
        "user",
    ).prefetch_related(
        "analyses",
    )

    rows = []

    for user_bond in user_bonds:
        analysis = get_latest_analysis(user_bond)

        if analysis is None:
            position_value = ZERO
            modified_duration = ZERO
            risk_score = ZERO
            final_signal = BondAnalysis.Signal.REVIEW
            final_signal_label = "Επανεξέταση"
        else:
            position_value = analysis.position_value or ZERO
            modified_duration = analysis.modified_duration or ZERO
            risk_score = analysis.risk_score or ZERO
            final_signal = analysis.final_signal
            final_signal_label = analysis.get_final_signal_display()

        rows.append(
            {
                "user_bond": user_bond,
                "analysis": analysis,
                "position_value": position_value,
                "modified_duration": modified_duration,
                "risk_score": risk_score,
                "final_signal": final_signal,
                "final_signal_label": final_signal_label,
            }
        )

    total_value = sum(
        row["position_value"]
        for row in rows
    )

    portfolio_duration = ZERO
    portfolio_risk_score = ZERO
    signal_counts = {}

    for row in rows:
        if total_value > ZERO:
            weight = row["position_value"] / total_value
        else:
            weight = ZERO

        row["weight"] = weight
        row["weighted_duration"] = weight * row["modified_duration"]
        row["weighted_risk"] = weight * row["risk_score"]

        portfolio_duration += row["weighted_duration"]
        portfolio_risk_score += row["weighted_risk"]

        signal_label = row["final_signal_label"]
        signal_counts[signal_label] = signal_counts.get(signal_label, 0) + 1

    portfolio_risk_level = get_portfolio_risk_level(portfolio_risk_score)

    return {
        "total_value": quantize_decimal(total_value),
        "portfolio_duration": quantize_decimal(portfolio_duration),
        "portfolio_risk_score": quantize_decimal(
            portfolio_risk_score,
            "0.0001",
        ),
        "portfolio_risk_level": portfolio_risk_level,
        "portfolio_risk_level_label": get_portfolio_risk_level_label(
            portfolio_risk_level,
        ),
        "bond_count": len(rows),
        "signal_counts": signal_counts,
    }