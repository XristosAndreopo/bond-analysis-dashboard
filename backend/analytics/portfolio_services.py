"""
Portfolio analytics services.

This module contains backend-side calculations for portfolio-level bond
analytics. The frontend should display these results, not calculate them.

The service calculates:
- portfolio rows with FX-adjusted weights
- total portfolio value in base currency
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
    FX conversion is manual for the MVP. If an FX rate is missing, the service
    returns warnings and excludes the missing converted amount from base-currency
    totals until the rate is provided.
"""

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from bonds.models import FXRate
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


def normalize_currency(currency):
    """
    Normalize a currency code.

    Args:
        currency: Currency string.

    Returns:
        Uppercase 3-letter currency code or empty string.
    """
    if not currency:
        return ""

    return str(currency).upper().strip()


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


def get_fx_rate_to_base(source_currency, portfolio_base_currency):
    """
    Get the FX rate used to convert source currency into portfolio base currency.

    Example direct rate:
        source_currency = USD
        portfolio_base_currency = EUR
        FXRate: 1 USD = 0.92 EUR
        return 0.92

    If no direct rate exists, the service tries to use the inverse rate.

    Args:
        source_currency: Currency being converted from.
        portfolio_base_currency: Currency being converted to.

    Returns:
        Dict with:
            rate: Decimal or None
            is_missing: bool
            method: SAME, DIRECT, INVERSE, MISSING
    """
    source_currency = normalize_currency(source_currency)
    portfolio_base_currency = normalize_currency(portfolio_base_currency)

    if not source_currency or not portfolio_base_currency:
        return {
            "rate": None,
            "is_missing": True,
            "method": "MISSING",
        }

    if source_currency == portfolio_base_currency:
        return {
            "rate": ONE,
            "is_missing": False,
            "method": "SAME",
        }

    direct_rate = FXRate.objects.filter(
        base_currency=source_currency,
        quote_currency=portfolio_base_currency,
    ).order_by(
        "-rate_date",
        "-created_at",
    ).first()

    if direct_rate is not None:
        return {
            "rate": direct_rate.rate,
            "is_missing": False,
            "method": "DIRECT",
        }

    inverse_rate = FXRate.objects.filter(
        base_currency=portfolio_base_currency,
        quote_currency=source_currency,
    ).order_by(
        "-rate_date",
        "-created_at",
    ).first()

    if inverse_rate is not None and inverse_rate.rate != ZERO:
        return {
            "rate": ONE / inverse_rate.rate,
            "is_missing": False,
            "method": "INVERSE",
        }

    return {
        "rate": None,
        "is_missing": True,
        "method": "MISSING",
    }


def convert_amount_to_base(amount, source_currency, portfolio_base_currency):
    """
    Convert an amount into the portfolio base currency.

    Args:
        amount: Decimal amount in original currency.
        source_currency: Original currency.
        portfolio_base_currency: Target portfolio currency.

    Returns:
        Dict with converted amount and FX metadata.
    """
    decimal_amount = safe_decimal(amount) or ZERO
    fx_result = get_fx_rate_to_base(
        source_currency=source_currency,
        portfolio_base_currency=portfolio_base_currency,
    )

    if fx_result["is_missing"]:
        return {
            "original_value": decimal_amount,
            "converted_value": None,
            "fx_rate_to_base": None,
            "fx_rate_missing": True,
            "fx_method": fx_result["method"],
        }

    converted_value = decimal_amount * fx_result["rate"]

    return {
        "original_value": decimal_amount,
        "converted_value": quantize_decimal(converted_value, "0.000001"),
        "fx_rate_to_base": quantize_decimal(fx_result["rate"], "0.00000001"),
        "fx_rate_missing": False,
        "fx_method": fx_result["method"],
    }


def calculate_portfolio_analytics(user, portfolio_base_currency="EUR"):
    """
    Calculate full backend portfolio analytics for a user.

    Args:
        user: Django user.
        portfolio_base_currency: Currency used for portfolio-level totals.

    Returns:
        Dict with summary, rows, and portfolio metrics.
    """
    portfolio_base_currency = normalize_currency(portfolio_base_currency) or "EUR"

    portfolio_items = list(get_active_portfolio_items(user))
    normalized_items = build_normalized_items(
        portfolio_items=portfolio_items,
        portfolio_base_currency=portfolio_base_currency,
    )
    total_value_base = calculate_total_converted_value(normalized_items)

    rows = build_portfolio_rows(
        normalized_items=normalized_items,
        total_value_base=total_value_base,
        portfolio_base_currency=portfolio_base_currency,
    )

    normalized_items_with_weights = attach_weights_to_normalized_items(
        normalized_items=normalized_items,
        rows=rows,
    )

    metrics = build_portfolio_metrics(
        normalized_items=normalized_items_with_weights,
        total_value_base=total_value_base,
        portfolio_base_currency=portfolio_base_currency,
    )

    summary = {
        "total_value": quantize_decimal(total_value_base, "0.01") or ZERO,
        "portfolio_base_currency": portfolio_base_currency,
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


def build_normalized_items(portfolio_items, portfolio_base_currency):
    """
    Build normalized item dictionaries used by all calculations.

    Args:
        portfolio_items: Iterable of UserBond instances.
        portfolio_base_currency: Portfolio base currency.

    Returns:
        List of normalized dicts.
    """
    normalized_items = []

    for user_bond in portfolio_items:
        analysis = get_latest_analysis(user_bond)
        market_data = get_latest_market_data(user_bond)
        bond_currency = normalize_currency(user_bond.bond.currency)

        original_position_value = (
            safe_decimal(analysis.position_value)
            if analysis is not None
            else safe_decimal(user_bond.position_value)
        ) or ZERO

        position_conversion = convert_amount_to_base(
            amount=original_position_value,
            source_currency=bond_currency,
            portfolio_base_currency=portfolio_base_currency,
        )

        estimated_annual_coupon = calculate_estimated_annual_coupon(user_bond)

        coupon_conversion = convert_amount_to_base(
            amount=estimated_annual_coupon,
            source_currency=bond_currency,
            portfolio_base_currency=portfolio_base_currency,
        )

        normalized_items.append(
            {
                "item": user_bond,
                "bond": user_bond.bond,
                "analysis": analysis,
                "market_data": market_data,
                "original_currency": bond_currency,
                "portfolio_base_currency": portfolio_base_currency,
                "original_position_value": original_position_value,
                "converted_position_value": position_conversion[
                    "converted_value"
                ],
                "fx_rate_to_base": position_conversion["fx_rate_to_base"],
                "fx_rate_missing": position_conversion["fx_rate_missing"],
                "fx_method": position_conversion["fx_method"],
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
                "estimated_annual_coupon": estimated_annual_coupon,
                "estimated_annual_coupon_base": coupon_conversion[
                    "converted_value"
                ],
                "coupon_fx_missing": coupon_conversion["fx_rate_missing"],
            }
        )

    return normalized_items


def calculate_total_converted_value(normalized_items):
    """
    Calculate total portfolio value in base currency.

    Args:
        normalized_items: Normalized item dicts.

    Returns:
        Decimal total converted value.
    """
    return sum(
        item["converted_position_value"] or ZERO
        for item in normalized_items
    )


def build_portfolio_rows(
    normalized_items,
    total_value_base,
    portfolio_base_currency,
):
    """
    Build rows consumed by PortfolioRowSerializer.

    Args:
        normalized_items: Normalized item dicts.
        total_value_base: Total portfolio value in base currency.
        portfolio_base_currency: Portfolio base currency.

    Returns:
        List of portfolio row dicts.
    """
    rows = []

    for normalized_item in normalized_items:
        analysis = normalized_item["analysis"]
        converted_position_value = normalized_item["converted_position_value"]

        if total_value_base > ZERO and converted_position_value is not None:
            weight = converted_position_value / total_value_base
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
                "original_position_value": quantize_decimal(
                    normalized_item["original_position_value"],
                    "0.000001",
                )
                or ZERO,
                "original_currency": normalized_item["original_currency"],
                "converted_position_value": quantize_decimal(
                    converted_position_value,
                    "0.000001",
                ),
                "portfolio_base_currency": portfolio_base_currency,
                "fx_rate_to_base": normalized_item["fx_rate_to_base"],
                "fx_rate_missing": normalized_item["fx_rate_missing"],
                "fx_method": normalized_item["fx_method"],
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


def build_portfolio_metrics(
    normalized_items,
    total_value_base,
    portfolio_base_currency,
):
    """
    Build full portfolio metric dictionary.

    Args:
        normalized_items: Normalized item dicts.
        total_value_base: Total value in base currency.
        portfolio_base_currency: Portfolio base currency.

    Returns:
        Dict of portfolio metrics.
    """
    currency_exposure = build_currency_exposure(
        normalized_items=normalized_items,
        total_value_base=total_value_base,
    )

    coupon_income_by_currency = build_coupon_income_by_currency(
        normalized_items=normalized_items,
        portfolio_base_currency=portfolio_base_currency,
    )

    missing_fx_rates = build_missing_fx_rate_list(
        normalized_items=normalized_items,
        portfolio_base_currency=portfolio_base_currency,
    )

    has_missing_fx_rates = len(missing_fx_rates) > 0

    estimated_annual_coupon_income_base = sum(
        item["estimated_annual_coupon_base"] or ZERO
        for item in normalized_items
    )

    weighted_risk_score = calculate_weighted_average(
        normalized_items,
        value_key="risk_score",
        weight_key="weight",
    )

    return {
        "portfolio_base_currency": portfolio_base_currency,
        "total_value_base": quantize_decimal(total_value_base, "0.01") or ZERO,
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
        "estimated_annual_coupon_income": quantize_decimal(
            estimated_annual_coupon_income_base,
            "0.01",
        )
        or ZERO,
        "estimated_annual_coupon_income_by_currency": coupon_income_by_currency,
        "main_currency": portfolio_base_currency,
        "has_mixed_currencies": len(currency_exposure) > 1,
        "has_missing_fx_rates": has_missing_fx_rates,
        "missing_fx_rates": missing_fx_rates,
        "currency_exposure": currency_exposure,
        "top_position": get_top_position(normalized_items),
        "highest_risk_position": get_highest_risk_position(normalized_items),
        "best_value_position": get_best_value_position(normalized_items),
        "signal_distribution": build_signal_distribution(normalized_items),
        "risk_distribution": build_risk_distribution(normalized_items),
        "mixed_currency_warning": build_fx_warning(
            portfolio_base_currency=portfolio_base_currency,
            missing_fx_rates=missing_fx_rates,
        ),
    }


def build_fx_warning(portfolio_base_currency, missing_fx_rates):
    """
    Build warning text for missing FX rates.

    Args:
        portfolio_base_currency: Portfolio base currency.
        missing_fx_rates: List of missing currency pairs.

    Returns:
        Warning string.
    """
    if not missing_fx_rates:
        return ""

    pairs = ", ".join(missing_fx_rates)

    return (
        "Λείπουν ισοτιμίες FX για μετατροπή σε "
        f"{portfolio_base_currency}: {pairs}. "
        "Οι θέσεις χωρίς FX rate δεν συμμετέχουν στο converted total value "
        "μέχρι να προστεθεί η αντίστοιχη ισοτιμία."
    )


def build_missing_fx_rate_list(normalized_items, portfolio_base_currency):
    """
    Build a unique list of missing FX currency pairs.

    Args:
        normalized_items: Normalized item dicts.
        portfolio_base_currency: Portfolio base currency.

    Returns:
        List of pair labels, e.g. ["USD/EUR"].
    """
    missing_pairs = set()

    for item in normalized_items:
        if item["fx_rate_missing"]:
            missing_pairs.add(
                f"{item['original_currency']}/{portfolio_base_currency}"
            )

    return sorted(missing_pairs)


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
        Decimal annual net coupon income in the bond's original currency.
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


def build_currency_exposure(normalized_items, total_value_base):
    """
    Build currency exposure list.

    Args:
        normalized_items: Normalized item dicts.
        total_value_base: Total converted portfolio value.

    Returns:
        List of currency exposure dicts.
    """
    exposure_by_currency = defaultdict(
        lambda: {
            "original_value": ZERO,
            "converted_value": ZERO,
        }
    )

    for item in normalized_items:
        currency = item["original_currency"] or "N/A"
        exposure_by_currency[currency]["original_value"] += (
            item["original_position_value"] or ZERO
        )
        exposure_by_currency[currency]["converted_value"] += (
            item["converted_position_value"] or ZERO
        )

    exposure_rows = []

    for currency, values in exposure_by_currency.items():
        converted_value = values["converted_value"]

        if total_value_base > ZERO:
            weight = converted_value / total_value_base
        else:
            weight = ZERO

        exposure_rows.append(
            {
                "currency": currency,
                "original_value": quantize_decimal(
                    values["original_value"],
                    "0.01",
                )
                or ZERO,
                "converted_value": quantize_decimal(
                    converted_value,
                    "0.01",
                )
                or ZERO,
                "weight": quantize_decimal(weight, "0.000001") or ZERO,
            }
        )

    return sorted(
        exposure_rows,
        key=lambda row: row["converted_value"],
        reverse=True,
    )


def build_coupon_income_by_currency(
    normalized_items,
    portfolio_base_currency,
):
    """
    Build estimated annual coupon income grouped by original currency.

    Args:
        normalized_items: Normalized item dicts.
        portfolio_base_currency: Portfolio base currency.

    Returns:
        List of coupon income rows.
    """
    income_by_currency = defaultdict(
        lambda: {
            "original_value": ZERO,
            "converted_value": ZERO,
        }
    )

    for item in normalized_items:
        currency = item["original_currency"] or "N/A"
        income_by_currency[currency]["original_value"] += (
            item["estimated_annual_coupon"] or ZERO
        )
        income_by_currency[currency]["converted_value"] += (
            item["estimated_annual_coupon_base"] or ZERO
        )

    rows = []

    for currency, values in income_by_currency.items():
        rows.append(
            {
                "currency": currency,
                "original_value": quantize_decimal(
                    values["original_value"],
                    "0.01",
                )
                or ZERO,
                "converted_value": quantize_decimal(
                    values["converted_value"],
                    "0.01",
                )
                or ZERO,
                "portfolio_base_currency": portfolio_base_currency,
            }
        )

    return sorted(
        rows,
        key=lambda row: row["converted_value"],
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