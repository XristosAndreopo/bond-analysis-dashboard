"""
Watchlist analytics services.

This module calculates FX-aware watchlist rows.

Purpose:
    The Watchlist is not only a list of bonds. It is a decision-support area
    where the user evaluates whether a bond is worth buying.

For that reason, the Watchlist should show:
- market price in the bond currency
- converted market price in the selected base currency
- FX rate used
- FX missing warning
- latest analytical signal
- latest risk level

Important:
    The frontend displays the result. The backend performs the calculation.
"""

from portfolios.models import UserBond
from analytics.portfolio_services import (
    convert_amount_to_base,
    normalize_currency,
    quantize_decimal,
    safe_decimal,
)


ZERO = safe_decimal("0")


def get_active_watchlist_items(user):
    """
    Return active Watchlist items for a user.

    Args:
        user: Django user.

    Returns:
        QuerySet of active Watchlist UserBond records.
    """
    return UserBond.objects.filter(
        user=user,
        is_active=True,
        holding_type=UserBond.HoldingType.WATCHLIST,
    ).select_related(
        "user",
        "bond",
    ).prefetch_related(
        "analyses",
        "analyses__cash_flows",
    )


def get_latest_market_data(user_bond):
    """
    Return the latest market data for a Watchlist item.

    Args:
        user_bond: UserBond instance.

    Returns:
        BondMarketData instance or None.
    """
    return user_bond.latest_market_data


def get_latest_analysis(user_bond):
    """
    Return the latest analysis for a Watchlist item.

    Args:
        user_bond: UserBond instance.

    Returns:
        BondAnalysis instance or None.
    """
    return user_bond.analyses.order_by(
        "-analysis_date",
        "-created_at",
    ).first()


def calculate_watchlist_analytics(user, portfolio_base_currency="EUR"):
    """
    Calculate FX-aware Watchlist analytics.

    Args:
        user: Django user.
        portfolio_base_currency: Selected base currency.

    Returns:
        Dict with watchlist rows and simple metrics.
    """
    portfolio_base_currency = normalize_currency(portfolio_base_currency) or "EUR"
    watchlist_items = list(get_active_watchlist_items(user))

    rows = []

    for user_bond in watchlist_items:
        bond = user_bond.bond
        market_data = get_latest_market_data(user_bond)
        original_currency = normalize_currency(bond.currency)

        original_market_price = (
            safe_decimal(market_data.market_price)
            if market_data is not None
            else None
        )

        conversion_result = convert_amount_to_base(
            amount=original_market_price or ZERO,
            source_currency=original_currency,
            portfolio_base_currency=portfolio_base_currency,
        )

        rows.append(
            {
                "user_bond": user_bond,
                "original_market_price": quantize_decimal(
                    original_market_price,
                    "0.000001",
                ),
                "original_currency": original_currency,
                "converted_market_price": (
                    quantize_decimal(
                        conversion_result["converted_value"],
                        "0.000001",
                    )
                    if original_market_price is not None
                    else None
                ),
                "portfolio_base_currency": portfolio_base_currency,
                "fx_rate_to_base": conversion_result["fx_rate_to_base"],
                "fx_rate_missing": (
                    conversion_result["fx_rate_missing"]
                    if original_market_price is not None
                    else False
                ),
                "fx_method": conversion_result["fx_method"],
            }
        )

    missing_fx_pairs = build_missing_fx_pairs(
        rows=rows,
        portfolio_base_currency=portfolio_base_currency,
    )

    return {
        "rows": rows,
        "metrics": {
            "portfolio_base_currency": portfolio_base_currency,
            "watchlist_count": len(rows),
            "has_missing_fx_rates": len(missing_fx_pairs) > 0,
            "missing_fx_rates": missing_fx_pairs,
            "fx_warning": build_fx_warning(
                portfolio_base_currency=portfolio_base_currency,
                missing_fx_pairs=missing_fx_pairs,
            ),
        },
    }


def build_missing_fx_pairs(rows, portfolio_base_currency):
    """
    Build a unique list of missing FX pairs.

    Args:
        rows: Watchlist row dictionaries.
        portfolio_base_currency: Target currency.

    Returns:
        List of missing pairs.
    """
    missing_pairs = set()

    for row in rows:
        if row["fx_rate_missing"]:
            missing_pairs.add(
                f"{row['original_currency']}/{portfolio_base_currency}"
            )

    return sorted(missing_pairs)


def build_fx_warning(portfolio_base_currency, missing_fx_pairs):
    """
    Build a user-facing warning for missing FX rates.

    Args:
        portfolio_base_currency: Target currency.
        missing_fx_pairs: Missing currency pairs.

    Returns:
        Warning text.
    """
    if not missing_fx_pairs:
        return ""

    pairs = ", ".join(missing_fx_pairs)

    return (
        f"Λείπουν ισοτιμίες για μετατροπή σε {portfolio_base_currency}: "
        f"{pairs}. Πήγαινε στη σελίδα FX Rates και πάτησε Update FX Rates."
    )