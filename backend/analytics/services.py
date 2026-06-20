"""
Bond analysis calculation services.

This module contains the core business logic for calculating bond valuation,
duration, risk, signals, and cash flows.

The frontend must not trigger a "Run Analysis" action. Instead, analysis is
automatically recalculated when market data or a user's bond position changes.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from analytics.models import BondAnalysis, CashFlow
from bonds.models import Bond, BondMarketData
from portfolios.models import UserBond


ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def quantize_decimal(value, places="0.000001"):
    """
    Safely quantize a Decimal value.

    Args:
        value: Decimal or None.
        places: Decimal precision pattern.

    Returns:
        Decimal or None.
    """
    if value is None:
        return None

    return Decimal(value).quantize(
        Decimal(places),
        rounding=ROUND_HALF_UP,
    )


def percentage_to_decimal(value):
    """
    Convert a percentage value into decimal form.

    Example:
        4.25 becomes 0.0425
    """
    if value is None:
        return None

    return Decimal(value) / HUNDRED


def add_months(source_date, months):
    """
    Add or subtract months from a date.

    This helper avoids adding new dependencies at this stage. It is useful for
    generating approximate coupon payment schedules.
    """
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1

    last_day = calendar.monthrange(year, month)[1]
    day = min(source_date.day, last_day)

    return date(year, month, day)


def generate_payment_dates(as_of_date, maturity_date, frequency):
    """
    Generate future coupon payment dates.

    The calculation assumes standard coupon frequencies such as 1, 2, 4, or 12.
    For non-standard frequencies, it falls back to an approximate day-based
    schedule and always includes maturity date.
    """
    if maturity_date <= as_of_date:
        return []

    if frequency <= 0:
        return []

    if 12 % frequency == 0:
        months_between_payments = 12 // frequency
        payment_dates = []
        current_date = maturity_date
        max_iterations = 1200

        while current_date > as_of_date and len(payment_dates) < max_iterations:
            payment_dates.append(current_date)
            current_date = add_months(current_date, -months_between_payments)

        return sorted(payment_dates)

    period_days = max(1, round(365.25 / frequency))
    payment_dates = []
    current_date = as_of_date + timedelta(days=period_days)

    while current_date < maturity_date:
        payment_dates.append(current_date)
        current_date += timedelta(days=period_days)

    if maturity_date not in payment_dates:
        payment_dates.append(maturity_date)

    return payment_dates


def calculate_current_yield(bond, market_price):
    """
    Calculate current yield as annual coupon divided by market price.

    Returns:
        Current yield as percentage.
    """
    if market_price is None or market_price <= ZERO:
        return None

    annual_coupon = bond.face_value * percentage_to_decimal(
        bond.annual_coupon_rate,
    )

    return (annual_coupon / market_price) * HUNDRED


def calculate_approx_aytm(bond, market_price):
    """
    Calculate approximate annual yield to maturity.

    Formula:
        AYTM ≈ [Coupon + ((FV - Price) / Years)] / [(FV + Price) / 2]

    Returns:
        Approximate AYTM as percentage.
    """
    if market_price is None or market_price <= ZERO:
        return None

    years = bond.years_to_maturity

    if years <= ZERO:
        return None

    annual_coupon = bond.face_value * percentage_to_decimal(
        bond.annual_coupon_rate,
    )

    numerator = annual_coupon + ((bond.face_value - market_price) / years)
    denominator = (bond.face_value + market_price) / Decimal("2")

    if denominator <= ZERO:
        return None

    return (numerator / denominator) * HUNDRED


def get_analysis_quantity(user_bond):
    """
    Return the quantity used for cash flow display.

    Portfolio items use the actual quantity. Watchlist items use quantity 1,
    so the user can understand the cash flow profile of one bond.
    """
    if (
        user_bond.holding_type == UserBond.HoldingType.PORTFOLIO
        and user_bond.quantity > 0
    ):
        return Decimal(user_bond.quantity)

    return Decimal("1")


def calculate_discounted_cash_flows(user_bond, market_data):
    """
    Calculate intrinsic value, duration, and cash flow rows.

    Returns:
        dict with:
            intrinsic_value_per_bond
            macaulay_duration
            modified_duration
            cash_flow_rows
            calculation_notes
    """
    bond = user_bond.bond
    as_of_date = market_data.quote_date
    discount_rate_percent = market_data.effective_discount_rate
    notes = []

    if discount_rate_percent is None:
        return {
            "intrinsic_value_per_bond": None,
            "macaulay_duration": None,
            "modified_duration": None,
            "cash_flow_rows": [],
            "calculation_notes": (
                "Market required return and YTM are missing. "
                "Valuation cannot be calculated."
            ),
        }

    payment_dates = generate_payment_dates(
        as_of_date=as_of_date,
        maturity_date=bond.maturity_date,
        frequency=bond.coupon_frequency,
    )

    if not payment_dates:
        return {
            "intrinsic_value_per_bond": None,
            "macaulay_duration": None,
            "modified_duration": None,
            "cash_flow_rows": [],
            "calculation_notes": "No future cash flows exist for this bond.",
        }

    if 12 % bond.coupon_frequency != 0:
        notes.append(
            "Non-standard coupon frequency was approximated using a day-based "
            "payment schedule."
        )

    quantity = get_analysis_quantity(user_bond)
    coupon_tax_rate = percentage_to_decimal(user_bond.coupon_tax_percent)
    coupon_rate = percentage_to_decimal(bond.annual_coupon_rate)

    coupon_gross_per_bond = (
        bond.face_value * coupon_rate / Decimal(bond.coupon_frequency)
    )
    coupon_tax_per_bond = coupon_gross_per_bond * coupon_tax_rate
    coupon_net_per_bond = coupon_gross_per_bond - coupon_tax_per_bond

    annual_discount_rate = percentage_to_decimal(discount_rate_percent)
    period_discount_rate = annual_discount_rate / Decimal(bond.coupon_frequency)
    discount_base = ONE + period_discount_rate

    if discount_base <= ZERO:
        notes.append(
            "Discount rate produced a non-positive discount base. "
            "Discounted cash flows were not discounted."
        )

    intrinsic_value_per_bond = ZERO
    weighted_time_sum = ZERO
    cash_flow_rows = []

    for index, payment_date in enumerate(payment_dates, start=1):
        principal_per_bond = (
            bond.face_value if payment_date == bond.maturity_date else ZERO
        )
        total_cash_flow_per_bond = coupon_net_per_bond + principal_per_bond

        if discount_base > ZERO:
            discounted_cash_flow_per_bond = (
                total_cash_flow_per_bond / (discount_base ** index)
            )
        else:
            discounted_cash_flow_per_bond = total_cash_flow_per_bond

        intrinsic_value_per_bond += discounted_cash_flow_per_bond

        time_in_years = Decimal(index) / Decimal(bond.coupon_frequency)
        weighted_time_sum += time_in_years * discounted_cash_flow_per_bond

        cash_flow_rows.append(
            {
                "period_number": index,
                "payment_date": payment_date,
                "coupon_gross": coupon_gross_per_bond * quantity,
                "coupon_tax": coupon_tax_per_bond * quantity,
                "coupon_net": coupon_net_per_bond * quantity,
                "principal": principal_per_bond * quantity,
                "total_cash_flow": total_cash_flow_per_bond * quantity,
                "discounted_cash_flow": (
                    discounted_cash_flow_per_bond * quantity
                ),
            }
        )

    if intrinsic_value_per_bond > ZERO:
        macaulay_duration = weighted_time_sum / intrinsic_value_per_bond
    else:
        macaulay_duration = None

    if macaulay_duration is not None and discount_base > ZERO:
        modified_duration = macaulay_duration / discount_base
    else:
        modified_duration = None

    return {
        "intrinsic_value_per_bond": intrinsic_value_per_bond,
        "macaulay_duration": macaulay_duration,
        "modified_duration": modified_duration,
        "cash_flow_rows": cash_flow_rows,
        "calculation_notes": " ".join(notes),
    }


def calculate_rating_risk_score(credit_rating):
    """
    Convert credit rating into a risk score component.

    This is a simplified MVP scoring method. Later, it can be replaced by
    a more advanced rating mapping table.
    """
    if not credit_rating:
        return Decimal("30")

    rating = credit_rating.upper().strip()

    if rating.startswith("AAA"):
        return Decimal("0")
    if rating.startswith("AA"):
        return Decimal("5")
    if rating.startswith("A"):
        return Decimal("12")
    if rating.startswith("BBB"):
        return Decimal("20")
    if rating.startswith("BB"):
        return Decimal("35")
    if rating.startswith("B"):
        return Decimal("45")
    if rating.startswith("CCC") or rating.startswith("CC") or rating == "C":
        return Decimal("60")
    if rating in {"D", "SD", "RD"}:
        return Decimal("80")

    return Decimal("30")


def calculate_risk_score(user_bond, modified_duration, market_data):
    """
    Calculate the total risk score for a user bond.

    Risk score is calculated on a 0-100 scale using:
    - duration risk
    - credit rating risk
    - liquidity risk
    - callable risk
    - seniority risk
    - currency mismatch risk
    - price premium risk
    """
    bond = user_bond.bond

    duration_component = ZERO
    if modified_duration is not None:
        duration_component = min(
            Decimal(modified_duration) * Decimal("8"),
            Decimal("40"),
        )

    rating_component = calculate_rating_risk_score(bond.credit_rating)

    liquidity_component = {
        Bond.MarketLiquidity.HIGH: Decimal("0"),
        Bond.MarketLiquidity.MEDIUM: Decimal("10"),
        Bond.MarketLiquidity.LOW: Decimal("20"),
    }.get(bond.market_liquidity, Decimal("10"))

    callable_component = Decimal("7") if bond.is_callable else ZERO

    seniority_component = {
        Bond.Seniority.SENIOR_SECURED: Decimal("0"),
        Bond.Seniority.SENIOR_UNSECURED: Decimal("5"),
        Bond.Seniority.SUBORDINATED: Decimal("15"),
        Bond.Seniority.JUNIOR: Decimal("20"),
        Bond.Seniority.OTHER: Decimal("10"),
    }.get(bond.seniority, Decimal("10"))

    currency_component = (
        Decimal("10") if bond.currency != user_bond.base_currency else ZERO
    )

    price_premium_component = ZERO
    if market_data.market_price > bond.face_value * Decimal("1.05"):
        price_premium_component = Decimal("5")

    total_score = (
        duration_component
        + rating_component
        + liquidity_component
        + callable_component
        + seniority_component
        + currency_component
        + price_premium_component
    )

    return min(total_score, Decimal("100"))


def get_risk_level(risk_score):
    """
    Convert a numeric risk score into a human-readable risk level.
    """
    if risk_score <= Decimal("20"):
        return BondAnalysis.RiskLevel.VERY_LOW

    if risk_score <= Decimal("35"):
        return BondAnalysis.RiskLevel.LOW

    if risk_score <= Decimal("55"):
        return BondAnalysis.RiskLevel.MEDIUM

    if risk_score <= Decimal("75"):
        return BondAnalysis.RiskLevel.HIGH

    return BondAnalysis.RiskLevel.VERY_HIGH


def build_risk_reasoning(user_bond, risk_score, modified_duration):
    """
    Build a short explanation for the risk score.
    """
    bond = user_bond.bond
    reasons = []

    if modified_duration is not None:
        reasons.append(
            f"Modified duration is approximately "
            f"{quantize_decimal(modified_duration, '0.01')}, which affects "
            f"price sensitivity to yield changes."
        )

    if bond.credit_rating:
        reasons.append(f"Credit rating is {bond.credit_rating}.")
    else:
        reasons.append("Credit rating is missing, so a conservative penalty was applied.")

    if bond.market_liquidity == Bond.MarketLiquidity.LOW:
        reasons.append("Market liquidity is low.")
    elif bond.market_liquidity == Bond.MarketLiquidity.MEDIUM:
        reasons.append("Market liquidity is medium.")

    if bond.is_callable:
        reasons.append("The bond is callable, which adds reinvestment risk.")

    if bond.currency != user_bond.base_currency:
        reasons.append("Bond currency differs from investor base currency.")

    reasons.append(f"Final risk score is {quantize_decimal(risk_score, '0.01')}.")

    return " ".join(reasons)


def calculate_iv_delta_percent(intrinsic_value, market_price):
    """
    Calculate how much intrinsic value differs from market price in percentage.
    """
    if intrinsic_value is None or market_price is None or market_price <= ZERO:
        return None

    return ((intrinsic_value - market_price) / market_price) * HUNDRED


def determine_signal(user_bond, intrinsic_value, market_price, risk_score):
    """
    Determine the final analytical signal.

    The result is an educational analytical indication, not investment advice.
    """
    if intrinsic_value is None or market_price is None:
        return (
            BondAnalysis.Signal.REVIEW,
            (
                "Analysis requires review because market required return or "
                "YTM is missing."
            ),
        )

    threshold = user_bond.valuation_threshold_percent
    iv_delta_percent = calculate_iv_delta_percent(intrinsic_value, market_price)

    if iv_delta_percent is None:
        return (
            BondAnalysis.Signal.REVIEW,
            "Analysis requires review because market price is not valid.",
        )

    if user_bond.holding_type == UserBond.HoldingType.WATCHLIST:
        return determine_watchlist_signal(
            iv_delta_percent=iv_delta_percent,
            threshold=threshold,
            risk_score=risk_score,
        )

    return determine_portfolio_signal(
        iv_delta_percent=iv_delta_percent,
        threshold=threshold,
        risk_score=risk_score,
    )


def determine_watchlist_signal(iv_delta_percent, threshold, risk_score):
    """
    Determine signal for Watchlist items.
    """
    if risk_score >= Decimal("75"):
        return (
            BondAnalysis.Signal.DO_NOT_BUY_WAIT,
            (
                "The bond appears too risky for a new purchase based on the "
                "current risk score."
            ),
        )

    if iv_delta_percent >= threshold and risk_score <= Decimal("55"):
        if iv_delta_percent < Decimal("2"):
            return (
                BondAnalysis.Signal.BUY_LOW_YIELD,
                (
                    "Intrinsic value is slightly above market price, but the "
                    "valuation margin appears limited."
                ),
            )

        return (
            BondAnalysis.Signal.BUY,
            (
                "Intrinsic value is above market price and risk is within an "
                "acceptable range."
            ),
        )

    if iv_delta_percent >= threshold and risk_score <= Decimal("75"):
        return (
            BondAnalysis.Signal.BUY_WITH_CAUTION,
            (
                "Intrinsic value is above market price, but the risk score "
                "requires caution."
            ),
        )

    if iv_delta_percent >= -threshold:
        return (
            BondAnalysis.Signal.REVIEW,
            (
                "The bond is close to fair value. More review is required "
                "before making a decision."
            ),
        )

    return (
        BondAnalysis.Signal.DO_NOT_BUY_WAIT,
        (
            "Market price appears higher than intrinsic value based on the "
            "current assumptions."
        ),
    )


def determine_portfolio_signal(iv_delta_percent, threshold, risk_score):
    """
    Determine signal for Portfolio items.
    """
    if risk_score >= Decimal("85"):
        return (
            BondAnalysis.Signal.SELL,
            (
                "Risk score is very high, so the position should be reviewed "
                "for possible sale."
            ),
        )

    if risk_score >= Decimal("70"):
        return (
            BondAnalysis.Signal.PARTIAL_SELL,
            (
                "Risk score is high, so reducing part of the position may be "
                "considered."
            ),
        )

    if iv_delta_percent >= threshold and risk_score <= Decimal("55"):
        return (
            BondAnalysis.Signal.BUY_MORE,
            (
                "Intrinsic value is above market price and risk is not high, "
                "so adding more may be considered."
            ),
        )

    if iv_delta_percent < -threshold and risk_score >= Decimal("55"):
        return (
            BondAnalysis.Signal.PARTIAL_SELL,
            (
                "Market price appears above intrinsic value and risk is not "
                "low, so partial selling may be considered."
            ),
        )

    if iv_delta_percent < -threshold:
        return (
            BondAnalysis.Signal.HOLD,
            (
                "Market price appears above intrinsic value, but risk is not "
                "high enough to justify a stronger signal."
            ),
        )

    return (
        BondAnalysis.Signal.HOLD,
        (
            "The position appears broadly balanced based on current valuation "
            "and risk assumptions."
        ),
    )


def calculate_net_ytm(user_bond, market_data, approx_aytm):
    """
    Calculate an estimated net YTM after coupon taxation.

    If provider YTM exists, it is preferred. Otherwise approximate AYTM is used.
    """
    gross_yield = market_data.ytm if market_data.ytm is not None else approx_aytm

    if gross_yield is None:
        return None

    tax_rate = percentage_to_decimal(user_bond.coupon_tax_percent)

    return gross_yield * (ONE - tax_rate)


def calculate_rcy(user_bond, current_yield, net_ytm):
    """
    Calculate a simplified reinvested coupon yield indicator.

    For the MVP, this is a conservative approximation. A more detailed RCY
    model can be added later with explicit reinvestment assumptions.
    """
    if not user_bond.reinvest_coupons:
        return current_yield

    if net_ytm is not None:
        return net_ytm

    return current_yield


def calculate_position_value(user_bond, market_data):
    """
    Calculate total position value for Portfolio items.

    Watchlist items return zero because the user does not own the bond.
    """
    if user_bond.holding_type != UserBond.HoldingType.PORTFOLIO:
        return ZERO

    return Decimal(user_bond.quantity) * market_data.market_price


@transaction.atomic
def analyze_user_bond(user_bond, market_data=None):
    """
    Calculate and save analysis for one UserBond.

    Args:
        user_bond: UserBond instance.
        market_data: Optional BondMarketData instance. If not provided, the
            latest market data for the bond is used.

    Returns:
        BondAnalysis instance.
    """
    if market_data is None:
        market_data = user_bond.latest_market_data

    analysis_date = (
        market_data.quote_date if market_data is not None else timezone.localdate()
    )

    if market_data is None:
        analysis, _ = BondAnalysis.objects.update_or_create(
            user_bond=user_bond,
            analysis_date=analysis_date,
            defaults={
                "market_data": None,
                "risk_score": ZERO,
                "risk_level": BondAnalysis.RiskLevel.MEDIUM,
                "position_value": ZERO,
                "final_signal": BondAnalysis.Signal.REVIEW,
                "reasoning": (
                    "No market data exists yet. Analysis cannot be calculated."
                ),
                "risk_reasoning": "Risk cannot be calculated without market data.",
                "calculation_notes": "Missing market data.",
            },
        )
        analysis.cash_flows.all().delete()
        return analysis

    cash_flow_result = calculate_discounted_cash_flows(
        user_bond=user_bond,
        market_data=market_data,
    )

    intrinsic_value = cash_flow_result["intrinsic_value_per_bond"]
    macaulay_duration = cash_flow_result["macaulay_duration"]
    modified_duration = cash_flow_result["modified_duration"]

    market_price = market_data.market_price
    current_yield = calculate_current_yield(user_bond.bond, market_price)
    approx_aytm = calculate_approx_aytm(user_bond.bond, market_price)
    net_ytm = calculate_net_ytm(user_bond, market_data, approx_aytm)
    rcy = calculate_rcy(user_bond, current_yield, net_ytm)

    if intrinsic_value is not None:
        iv_vs_market_price = intrinsic_value - market_price
    else:
        iv_vs_market_price = None

    cost_basis = user_bond.purchase_price or market_price

    if intrinsic_value is not None and cost_basis > ZERO:
        iv_to_cost = intrinsic_value / cost_basis
    else:
        iv_to_cost = None

    if modified_duration is not None:
        yield_change_decimal = percentage_to_decimal(
            user_bond.expected_yield_change,
        )
        price_impact = -modified_duration * yield_change_decimal * market_price
        estimated_price = market_price + price_impact
    else:
        price_impact = None
        estimated_price = None

    risk_score = calculate_risk_score(
        user_bond=user_bond,
        modified_duration=modified_duration,
        market_data=market_data,
    )
    risk_level = get_risk_level(risk_score)
    risk_reasoning = build_risk_reasoning(
        user_bond=user_bond,
        risk_score=risk_score,
        modified_duration=modified_duration,
    )

    final_signal, reasoning = determine_signal(
        user_bond=user_bond,
        intrinsic_value=intrinsic_value,
        market_price=market_price,
        risk_score=risk_score,
    )

    position_value = calculate_position_value(
        user_bond=user_bond,
        market_data=market_data,
    )

    analysis, _ = BondAnalysis.objects.update_or_create(
        user_bond=user_bond,
        analysis_date=analysis_date,
        defaults={
            "market_data": market_data,
            "intrinsic_value": quantize_decimal(intrinsic_value),
            "iv_to_cost": quantize_decimal(iv_to_cost),
            "iv_vs_market_price": quantize_decimal(iv_vs_market_price),
            "market_price_minus_face_value": quantize_decimal(
                market_price - user_bond.bond.face_value,
            ),
            "current_yield": quantize_decimal(current_yield),
            "net_ytm": quantize_decimal(net_ytm),
            "approx_aytm": quantize_decimal(approx_aytm),
            "rcy": quantize_decimal(rcy),
            "macaulay_duration": quantize_decimal(macaulay_duration),
            "modified_duration": quantize_decimal(modified_duration),
            "price_impact": quantize_decimal(price_impact),
            "estimated_price": quantize_decimal(estimated_price),
            "risk_score": quantize_decimal(risk_score, "0.0001"),
            "risk_level": risk_level,
            "position_value": quantize_decimal(position_value),
            "final_signal": final_signal,
            "reasoning": reasoning,
            "risk_reasoning": risk_reasoning,
            "calculation_notes": cash_flow_result["calculation_notes"],
        },
    )

    analysis.cash_flows.all().delete()

    cash_flow_objects = [
        CashFlow(
            analysis=analysis,
            period_number=row["period_number"],
            payment_date=row["payment_date"],
            coupon_gross=quantize_decimal(row["coupon_gross"]),
            coupon_tax=quantize_decimal(row["coupon_tax"]),
            coupon_net=quantize_decimal(row["coupon_net"]),
            principal=quantize_decimal(row["principal"]),
            total_cash_flow=quantize_decimal(row["total_cash_flow"]),
            discounted_cash_flow=quantize_decimal(row["discounted_cash_flow"]),
        )
        for row in cash_flow_result["cash_flow_rows"]
    ]

    CashFlow.objects.bulk_create(cash_flow_objects)

    return analysis


def analyze_bond_for_all_users(bond, market_data=None):
    """
    Recalculate analysis for all active user bonds connected to a bond.

    This is used when new market data is saved.
    """
    user_bonds = UserBond.objects.filter(
        bond=bond,
        is_active=True,
    ).select_related(
        "user",
        "bond",
    )

    analyses = []

    for user_bond in user_bonds:
        analyses.append(
            analyze_user_bond(
                user_bond=user_bond,
                market_data=market_data,
            )
        )

    return analyses