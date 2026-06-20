"""
Portfolio analytics services.

This module contains backend-side calculations for portfolio-level bond
analytics. The frontend should display these results, not calculate them.

The service calculates:
- portfolio rows with weights
- weighted average YTM
- weighted current yield
- weighted modified duration
- weighted risk score
- portfolio concentration
- estimated annual coupon income
- currency exposure
- top position
- highest risk position
- best value position
- signal distribution
- risk distribution

Important:
    FX conversion is not implemented yet. If the portfolio contains multiple
    currencies, values are grouped by currency and a mixed-currency warning is
    returned.
"""

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from portfolios.models import UserBond


ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def safe_decimal(value):
    """
    Convert a value to Decimal safely.

    Args:
        value: Any numeric-like value.

    Returns:
        Decimal or None.
    """
    if value is None or value == "":
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def quantize_decimal(value, places="0.000001"):
    """
    Quantize a Decimal value safely.

    Args:
        value: Decimal-like value.
        places: Decimal quantization pattern.

    Returns:
        Quantized Decimal or None.
    """
    decimal_value = safe_decimal(value)

    if decimal_value is None:
        return None

    return decimal_value.quantize(Decimal(places))


def get_active_portfolio_items(user):
    """
    Return active Portfolio items for a user.

    Args:
        user: Django user.

    Returns:
        QuerySet of active portfolio UserBond records.
    """
    return UserBond.objects.filter(
        user=user,
        is_active=True,
        holding_type=UserBond.HoldingType.PORTFOLIO,
    ).select_related(
        "user",
        "bond",
    ).prefetch_related(
        "analyses",
        "analyses__cash_flows",
    )


def get_latest_analysis(user_bond):
    """
    Return the latest analysis for a UserBond.

    Args:
        user_bond: UserBond instance.

    Returns:
        BondAnalysis instance or None.
    """
    return user_bond.analyses.order_by(
        "-analysis_date",
        "-created_at",
    ).first()


def get_latest_market_data(user_bond):
    """
    Return latest market data for a UserBond.

    Args:
        user_bond: UserBond instance.

    Returns:
        BondMarketData instance or None.
    """
    return user_bond.latest_market_data


def calculate_portfolio_analytics(user):
    """
    Calculate full backend portfolio analytics for a user.

    Args:
        user: Django user.

    Returns:
        Dict with summary, rows, and portfolio metrics.
    """
    portfolio_items = list(get_active_portfolio_items(user))
    normalized_items = build_normalized_items(portfolio_items)
    total_value = calculate_total_value(normalized_items)

    rows = build_portfolio_rows(
        normalized_items=normalized_items,
        total_value=total_value,
    )

    normalized_items_with_weights = attach_weights_to_normalized_items(
        normalized_items=normalized_items,
        rows=rows,
    )

    metrics = build_portfolio_metrics(
        normalized_items=normalized_items_with_weights,
        total_value=total_value,
    )

    summary = {
        "total_value": quantize_decimal(total_value, "0.01") or ZERO,
        "portfolio_duration": quantize_decimal(
            metrics["weighted_modified_duration"],
            "0.000001",
        )
        or ZERO,
        "portfolio_risk_score": quantize_decimal(
            metrics["weighted_risk_score"],
            "0.000001",
        )
        or ZERO,
        "portfolio_risk_level": get_portfolio_risk_level(
            metrics["weighted_risk_score"]
        ),
        "portfolio_risk_level_label": get_portfolio_risk_level_label(
            metrics["weighted_risk_score"]
        ),
        "bond_count": len(portfolio_items),
    }

    return {
        "summary": summary,
        "rows": rows,
        "metrics": metrics,
    }


def build_normalized_items(portfolio_items):
    """
    Build normalized item dictionaries used by all calculations.

    Args:
        portfolio_items: Iterable of UserBond instances.

    Returns:
        List of normalized dicts.
    """
    normalized_items = []

    for user_bond in portfolio_items:
        analysis = get_latest_analysis(user_bond)
        market_data = get_latest_market_data(user_bond)

        position_value = (
            safe_decimal(analysis.position_value)
            if analysis is not None
            else safe_decimal(user_bond.position_value)
        )

        normalized_items.append(
            {
                "item": user_bond,
                "bond": user_bond.bond,
                "analysis": analysis,
                "market_data": market_data,
                "position_value": position_value or ZERO,
                "modified_duration": safe_decimal(
                    analysis.modified_duration if analysis else None
                ),
                "risk_score": safe_decimal(
                    analysis.risk_score if analysis else None
                ),
                "current_yield": safe_decimal(
                    analysis.current_yield if analysis else None
                ),
                "ytm": safe_decimal(market_data.ytm if market_data else None),
                "iv_vs_market_price": safe_decimal(
                    analysis.iv_vs_market_price if analysis else None
                ),
                "signal": analysis.final_signal if analysis else "REVIEW",
                "signal_label": (
                    analysis.get_final_signal_display()
                    if analysis
                    else "Επανεξέταση"
                ),
                "risk_level": analysis.risk_level if analysis else "UNKNOWN",
                "risk_level_label": (
                    analysis.get_risk_level_display()
                    if analysis
                    else "Άγνωστο"
                ),
                "estimated_annual_coupon": calculate_estimated_annual_coupon(
                    user_bond
                ),
            }
        )

    return normalized_items


def calculate_total_value(normalized_items):
    """
    Calculate total portfolio value.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        Decimal total value.
    """
    return sum(
        item["position_value"] or ZERO
        for item in normalized_items
    )


def build_portfolio_rows(normalized_items, total_value):
    """
    Build rows consumed by PortfolioRowSerializer.

    Args:
        normalized_items: Normalized item dicts.
        total_value: Total portfolio value.

    Returns:
        List of portfolio row dicts.
    """
    rows = []

    for normalized_item in normalized_items:
        analysis = normalized_item["analysis"]
        position_value = normalized_item["position_value"]

        if total_value > ZERO:
            weight = position_value / total_value
        else:
            weight = ZERO

        modified_duration = (
            safe_decimal(analysis.modified_duration)
            if analysis is not None
            else ZERO
        ) or ZERO

        risk_score = (
            safe_decimal(analysis.risk_score)
            if analysis is not None
            else ZERO
        ) or ZERO

        rows.append(
            {
                "user_bond": normalized_item["item"],
                "weight": quantize_decimal(weight, "0.000001") or ZERO,
                "weighted_duration": quantize_decimal(
                    weight * modified_duration,
                    "0.000001",
                )
                or ZERO,
                "weighted_risk": quantize_decimal(
                    weight * risk_score,
                    "0.000001",
                )
                or ZERO,
            }
        )

    return rows


def attach_weights_to_normalized_items(normalized_items, rows):
    """
    Attach row weights back to normalized items.

    Args:
        normalized_items: Normalized item dicts.
        rows: Portfolio row dicts.

    Returns:
        Normalized item dicts with weight fields.
    """
    weight_by_user_bond_id = {
        row["user_bond"].id: row["weight"]
        for row in rows
    }

    for normalized_item in normalized_items:
        normalized_item["weight"] = weight_by_user_bond_id.get(
            normalized_item["item"].id,
            ZERO,
        )

    return normalized_items


def build_portfolio_metrics(normalized_items, total_value):
    """
    Build full portfolio metric dictionary.

    Args:
        normalized_items: Normalized item dicts.
        total_value: Decimal total value.

    Returns:
        Dict of portfolio metrics.
    """
    currency_exposure = build_currency_exposure(
        normalized_items=normalized_items,
        total_value=total_value,
    )

    coupon_income_by_currency = build_coupon_income_by_currency(
        normalized_items
    )

    has_mixed_currencies = len(currency_exposure) > 1
    main_currency = currency_exposure[0]["currency"] if currency_exposure else ""

    estimated_annual_coupon_income = None

    if len(coupon_income_by_currency) == 1:
        estimated_annual_coupon_income = coupon_income_by_currency[0]["value"]

    weighted_risk_score = calculate_weighted_average(
        normalized_items,
        value_key="risk_score",
        weight_key="weight",
    )

    return {
        "weighted_average_ytm": calculate_weighted_average(
            normalized_items,
            value_key="ytm",
            weight_key="weight",
        ),
        "weighted_current_yield": calculate_weighted_average(
            normalized_items,
            value_key="current_yield",
            weight_key="weight",
        ),
        "weighted_modified_duration": calculate_weighted_average(
            normalized_items,
            value_key="modified_duration",
            weight_key="weight",
        ),
        "weighted_risk_score": weighted_risk_score,
        "portfolio_concentration": get_max_value(
            normalized_items,
            key="weight",
        ),
        "estimated_annual_coupon_income": estimated_annual_coupon_income,
        "estimated_annual_coupon_income_by_currency": coupon_income_by_currency,
        "main_currency": main_currency,
        "has_mixed_currencies": has_mixed_currencies,
        "currency_exposure": currency_exposure,
        "top_position": get_top_position(normalized_items),
        "highest_risk_position": get_highest_risk_position(normalized_items),
        "best_value_position": get_best_value_position(normalized_items),
        "signal_distribution": build_signal_distribution(normalized_items),
        "risk_distribution": build_risk_distribution(normalized_items),
        "mixed_currency_warning": (
            "Το Portfolio περιέχει περισσότερα από ένα νομίσματα. "
            "Τα συνολικά ποσά είναι ονομαστικά μέχρι να προστεθεί FX conversion."
            if has_mixed_currencies
            else ""
        ),
    }


def calculate_weighted_average(items, value_key, weight_key):
    """
    Calculate a weighted average.

    Args:
        items: Normalized item dicts.
        value_key: Value key.
        weight_key: Weight key.

    Returns:
        Decimal weighted average or None.
    """
    weighted_sum = ZERO
    total_weight = ZERO

    for item in items:
        value = item.get(value_key)
        weight = item.get(weight_key)

        if value is None or weight is None:
            continue

        weighted_sum += value * weight
        total_weight += weight

    if total_weight == ZERO:
        return None

    return quantize_decimal(weighted_sum / total_weight, "0.000001")


def get_max_value(items, key):
    """
    Return max Decimal value for a key.

    Args:
        items: Normalized item dicts.
        key: Dict key.

    Returns:
        Decimal max value or None.
    """
    values = [
        item[key]
        for item in items
        if item.get(key) is not None
    ]

    if not values:
        return None

    return max(values)


def calculate_estimated_annual_coupon(user_bond):
    """
    Estimate annual net coupon income for one UserBond position.

    Formula:
        face_value * annual_coupon_rate * quantity * (1 - coupon_tax)

    Rates are stored as percentages:
        3.875 means 3.875%

    Args:
        user_bond: UserBond instance.

    Returns:
        Decimal annual net coupon income.
    """
    face_value = safe_decimal(user_bond.bond.face_value)
    coupon_rate = safe_decimal(user_bond.bond.annual_coupon_rate)
    quantity = safe_decimal(user_bond.quantity)
    coupon_tax_percent = safe_decimal(user_bond.coupon_tax_percent) or ZERO

    if face_value is None or coupon_rate is None or quantity is None:
        return ZERO

    gross_coupon = face_value * (coupon_rate / HUNDRED) * quantity
    tax_amount = gross_coupon * (coupon_tax_percent / HUNDRED)

    return quantize_decimal(gross_coupon - tax_amount, "0.000001") or ZERO


def build_currency_exposure(normalized_items, total_value):
    """
    Build currency exposure list.

    Args:
        normalized_items: Normalized item dicts.
        total_value: Total portfolio value.

    Returns:
        List of currency exposure dicts.
    """
    exposure_by_currency = defaultdict(Decimal)

    for item in normalized_items:
        currency = item["bond"].currency or "N/A"
        exposure_by_currency[currency] += item["position_value"] or ZERO

    if total_value == ZERO:
        return []

    exposure_rows = []

    for currency, value in exposure_by_currency.items():
        exposure_rows.append(
            {
                "currency": currency,
                "value": quantize_decimal(value, "0.01") or ZERO,
                "weight": quantize_decimal(value / total_value, "0.000001")
                or ZERO,
            }
        )

    return sorted(
        exposure_rows,
        key=lambda row: row["value"],
        reverse=True,
    )


def build_coupon_income_by_currency(normalized_items):
    """
    Build estimated annual coupon income grouped by currency.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        List of coupon income rows.
    """
    income_by_currency = defaultdict(Decimal)

    for item in normalized_items:
        currency = item["bond"].currency or "N/A"
        income_by_currency[currency] += item["estimated_annual_coupon"] or ZERO

    rows = [
        {
            "currency": currency,
            "value": quantize_decimal(value, "0.01") or ZERO,
        }
        for currency, value in income_by_currency.items()
    ]

    return sorted(
        rows,
        key=lambda row: row["value"],
        reverse=True,
    )


def get_top_position(normalized_items):
    """
    Return the position with the largest portfolio weight.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        Normalized item dict or None.
    """
    candidates = [
        item
        for item in normalized_items
        if item.get("weight") is not None
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: item["weight"],
    )


def get_highest_risk_position(normalized_items):
    """
    Return the position with the highest risk score.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        Normalized item dict or None.
    """
    candidates = [
        item
        for item in normalized_items
        if item.get("risk_score") is not None
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: item["risk_score"],
    )


def get_best_value_position(normalized_items):
    """
    Return the position with the highest IV vs Market Price.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        Normalized item dict or None.
    """
    candidates = [
        item
        for item in normalized_items
        if item.get("iv_vs_market_price") is not None
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: item["iv_vs_market_price"],
    )


def build_signal_distribution(normalized_items):
    """
    Build signal distribution.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        List of distribution rows.
    """
    distribution = {}

    for item in normalized_items:
        signal = item["signal"]
        label = item["signal_label"]

        if signal not in distribution:
            distribution[signal] = {
                "key": signal,
                "label": label,
                "count": 0,
            }

        distribution[signal]["count"] += 1

    return list(distribution.values())


def build_risk_distribution(normalized_items):
    """
    Build risk distribution.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        List of distribution rows.
    """
    distribution = {}

    for item in normalized_items:
        risk_level = item["risk_level"]
        label = item["risk_level_label"]

        if risk_level not in distribution:
            distribution[risk_level] = {
                "key": risk_level,
                "label": label,
                "count": 0,
            }

        distribution[risk_level]["count"] += 1

    return list(distribution.values())


def get_portfolio_risk_level(weighted_risk_score):
    """
    Convert weighted risk score to portfolio risk level.

    Args:
        weighted_risk_score: Decimal risk score.

    Returns:
        Risk level code.
    """
    risk_score = safe_decimal(weighted_risk_score)

    if risk_score is None:
        return "UNKNOWN"

    if risk_score < Decimal("20"):
        return "VERY_LOW"

    if risk_score < Decimal("40"):
        return "LOW"

    if risk_score < Decimal("60"):
        return "MEDIUM"

    if risk_score < Decimal("80"):
        return "HIGH"

    return "VERY_HIGH"


def get_portfolio_risk_level_label(weighted_risk_score):
    """
    Convert weighted risk score to a display label.

    Args:
        weighted_risk_score: Decimal risk score.

    Returns:
        Display label.
    """
    risk_level = get_portfolio_risk_level(weighted_risk_score)

    labels = {
        "VERY_LOW": "Πολύ χαμηλό",
        "LOW": "Χαμηλό",
        "MEDIUM": "Μεσαίο",
        "HIGH": "Υψηλό",
        "VERY_HIGH": "Πολύ υψηλό",
        "UNKNOWN": "Άγνωστο",
    }

    return labels.get(risk_level, "Άγνωστο")