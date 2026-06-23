"""
Bond mathematics helpers used by discovery and AI research imports.

The functions in this module intentionally use only Python's standard
library and Decimal arithmetic. They are not a substitute for a professional
pricing engine, but they are sufficient for the MVP use case:

- calculate YTM when AI/CSV data provides price, coupon and maturity
- calculate modified duration when YTM is available or calculated
- keep traceability about which values were backend-calculated

Conventions:
    Coupon rates and YTM values are percentages.
    Example:
        4.125 means 4.125%, not 0.04125.

    Prices are per 100 face value unless another face value is passed.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import ceil
from typing import Any


ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
DEFAULT_FACE_VALUE = Decimal("100.0000")
DEFAULT_COUPON_FREQUENCY = 1


def safe_decimal(value: Any) -> Decimal | None:
    """
    Convert a value to Decimal safely.

    Args:
        value: Numeric-like value.

    Returns:
        Decimal or None.
    """
    if value is None or value == "":
        return None

    if isinstance(value, Decimal):
        return value

    normalized_value = str(value).strip().replace("%", "").replace(",", "")

    if not normalized_value:
        return None

    try:
        return Decimal(normalized_value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def quantize_decimal(value: Any, places: str = "0.000001") -> Decimal | None:
    """
    Quantize a Decimal value safely.

    Args:
        value: Numeric-like value.
        places: Decimal quantization pattern.

    Returns:
        Quantized Decimal or None.
    """
    decimal_value = safe_decimal(value)

    if decimal_value is None:
        return None

    return decimal_value.quantize(
        Decimal(places),
        rounding=ROUND_HALF_UP,
    )


def normalize_coupon_frequency(value: Any) -> int:
    """
    Normalize a coupon frequency value.

    Args:
        value: Raw coupon frequency.

    Returns:
        Integer frequency between 1 and 12.
    """
    try:
        frequency = int(value)
    except (TypeError, ValueError):
        return DEFAULT_COUPON_FREQUENCY

    if frequency < 1:
        return DEFAULT_COUPON_FREQUENCY

    if frequency > 12:
        return 12

    return frequency


def calculate_years_to_maturity(
    maturity_date: date | None,
    quote_date: date | None = None,
) -> Decimal | None:
    """
    Calculate approximate years to maturity.

    Args:
        maturity_date: Bond maturity date.
        quote_date: Valuation date.

    Returns:
        Decimal years or None.
    """
    if maturity_date is None:
        return None

    quote_date = quote_date or date.today()

    if maturity_date <= quote_date:
        return None

    days_to_maturity = Decimal((maturity_date - quote_date).days)

    return days_to_maturity / Decimal("365.25")


def build_cash_flow_times(
    maturity_date: date,
    quote_date: date | None = None,
    coupon_frequency: int = DEFAULT_COUPON_FREQUENCY,
) -> list[Decimal]:
    """
    Build approximate future cash flow times in years.

    The final cash flow is always placed at actual maturity. Intermediate
    times follow the coupon frequency.

    Args:
        maturity_date: Bond maturity date.
        quote_date: Valuation date.
        coupon_frequency: Coupon payments per year.

    Returns:
        List of year fractions.
    """
    years_to_maturity = calculate_years_to_maturity(
        maturity_date=maturity_date,
        quote_date=quote_date,
    )

    if years_to_maturity is None:
        return []

    coupon_frequency = normalize_coupon_frequency(coupon_frequency)
    estimated_period_count = int(ceil(float(years_to_maturity * coupon_frequency)))
    period_count = max(1, estimated_period_count)

    cash_flow_times = []

    for period_number in range(1, period_count + 1):
        period_time = Decimal(period_number) / Decimal(coupon_frequency)

        if period_number == period_count or period_time > years_to_maturity:
            period_time = years_to_maturity

        if period_time > ZERO:
            cash_flow_times.append(period_time)

    return cash_flow_times


def calculate_present_value_from_yield(
    annual_yield_percent: Decimal,
    coupon_rate_percent: Decimal,
    maturity_date: date,
    quote_date: date | None = None,
    face_value: Decimal = DEFAULT_FACE_VALUE,
    coupon_frequency: int = DEFAULT_COUPON_FREQUENCY,
) -> Decimal | None:
    """
    Calculate clean present value from an annual yield.

    Args:
        annual_yield_percent: Annual YTM as percentage.
        coupon_rate_percent: Annual coupon rate as percentage.
        maturity_date: Bond maturity date.
        quote_date: Valuation date.
        face_value: Face value.
        coupon_frequency: Coupon payments per year.

    Returns:
        Present value per face value or None.
    """
    annual_yield_percent = safe_decimal(annual_yield_percent)
    coupon_rate_percent = safe_decimal(coupon_rate_percent)
    face_value = safe_decimal(face_value) or DEFAULT_FACE_VALUE

    if annual_yield_percent is None or coupon_rate_percent is None:
        return None

    if face_value <= ZERO:
        return None

    coupon_frequency = normalize_coupon_frequency(coupon_frequency)
    cash_flow_times = build_cash_flow_times(
        maturity_date=maturity_date,
        quote_date=quote_date,
        coupon_frequency=coupon_frequency,
    )

    if not cash_flow_times:
        return None

    annual_yield_decimal = annual_yield_percent / HUNDRED
    periodic_yield = annual_yield_decimal / Decimal(coupon_frequency)

    if ONE + periodic_yield <= ZERO:
        return None

    coupon_payment = (
        face_value
        * (coupon_rate_percent / HUNDRED)
        / Decimal(coupon_frequency)
    )

    present_value = ZERO

    for index, time_in_years in enumerate(cash_flow_times, start=1):
        cash_flow = coupon_payment

        if index == len(cash_flow_times):
            cash_flow += face_value

        exponent = time_in_years * Decimal(coupon_frequency)
        present_value += cash_flow / ((ONE + periodic_yield) ** exponent)

    return present_value


def calculate_ytm(
    market_price: Any,
    coupon_rate: Any,
    maturity_date: date | None,
    quote_date: date | None = None,
    face_value: Any = DEFAULT_FACE_VALUE,
    coupon_frequency: Any = DEFAULT_COUPON_FREQUENCY,
) -> Decimal | None:
    """
    Calculate Yield to Maturity using a bisection root search.

    Args:
        market_price: Clean market price per face value.
        coupon_rate: Annual coupon rate as percentage.
        maturity_date: Bond maturity date.
        quote_date: Valuation date.
        face_value: Face value.
        coupon_frequency: Coupon payments per year.

    Returns:
        YTM as percentage or None.
    """
    market_price = safe_decimal(market_price)
    coupon_rate = safe_decimal(coupon_rate)
    face_value = safe_decimal(face_value) or DEFAULT_FACE_VALUE

    if market_price is None or market_price <= ZERO:
        return None

    if coupon_rate is None:
        return None

    if maturity_date is None:
        return None

    if calculate_years_to_maturity(maturity_date, quote_date) is None:
        return None

    coupon_frequency = normalize_coupon_frequency(coupon_frequency)

    lower_rate = Decimal("-95.000000")
    upper_rate = Decimal("100.000000")

    def pricing_error(rate_percent: Decimal) -> Decimal | None:
        present_value = calculate_present_value_from_yield(
            annual_yield_percent=rate_percent,
            coupon_rate_percent=coupon_rate,
            maturity_date=maturity_date,
            quote_date=quote_date,
            face_value=face_value,
            coupon_frequency=coupon_frequency,
        )

        if present_value is None:
            return None

        return present_value - market_price

    lower_error = pricing_error(lower_rate)
    upper_error = pricing_error(upper_rate)

    if lower_error is None or upper_error is None:
        return None

    expansion_attempts = 0

    while lower_error * upper_error > ZERO and expansion_attempts < 6:
        upper_rate *= Decimal("2")
        upper_error = pricing_error(upper_rate)

        if upper_error is None:
            return None

        expansion_attempts += 1

    if lower_error * upper_error > ZERO:
        return calculate_approximate_ytm(
            market_price=market_price,
            coupon_rate=coupon_rate,
            maturity_date=maturity_date,
            quote_date=quote_date,
            face_value=face_value,
        )

    for _iteration in range(120):
        midpoint_rate = (lower_rate + upper_rate) / Decimal("2")
        midpoint_error = pricing_error(midpoint_rate)

        if midpoint_error is None:
            return None

        if abs(midpoint_error) < Decimal("0.0000001"):
            return quantize_decimal(midpoint_rate, "0.00001")

        if lower_error * midpoint_error <= ZERO:
            upper_rate = midpoint_rate
            upper_error = midpoint_error
        else:
            lower_rate = midpoint_rate
            lower_error = midpoint_error

    return quantize_decimal((lower_rate + upper_rate) / Decimal("2"), "0.00001")


def calculate_approximate_ytm(
    market_price: Any,
    coupon_rate: Any,
    maturity_date: date | None,
    quote_date: date | None = None,
    face_value: Any = DEFAULT_FACE_VALUE,
) -> Decimal | None:
    """
    Calculate approximate YTM as fallback.

    Formula:
        Approx YTM = [Coupon + (FV - Price) / Years] / [(FV + Price) / 2]

    Args:
        market_price: Clean market price.
        coupon_rate: Annual coupon rate as percentage.
        maturity_date: Maturity date.
        quote_date: Valuation date.
        face_value: Face value.

    Returns:
        Approximate YTM as percentage or None.
    """
    market_price = safe_decimal(market_price)
    coupon_rate = safe_decimal(coupon_rate)
    face_value = safe_decimal(face_value) or DEFAULT_FACE_VALUE
    years_to_maturity = calculate_years_to_maturity(
        maturity_date=maturity_date,
        quote_date=quote_date,
    )

    if (
        market_price is None
        or coupon_rate is None
        or years_to_maturity is None
        or market_price <= ZERO
        or face_value <= ZERO
    ):
        return None

    annual_coupon = face_value * (coupon_rate / HUNDRED)
    numerator = annual_coupon + ((face_value - market_price) / years_to_maturity)
    denominator = (face_value + market_price) / Decimal("2")

    if denominator <= ZERO:
        return None

    return quantize_decimal((numerator / denominator) * HUNDRED, "0.00001")


def calculate_modified_duration(
    coupon_rate: Any,
    maturity_date: date | None,
    ytm: Any,
    quote_date: date | None = None,
    face_value: Any = DEFAULT_FACE_VALUE,
    coupon_frequency: Any = DEFAULT_COUPON_FREQUENCY,
) -> Decimal | None:
    """
    Calculate modified duration using discounted cash flows.

    Args:
        coupon_rate: Annual coupon rate as percentage.
        maturity_date: Bond maturity date.
        ytm: Annual YTM as percentage.
        quote_date: Valuation date.
        face_value: Face value.
        coupon_frequency: Coupon payments per year.

    Returns:
        Modified duration or None.
    """
    coupon_rate = safe_decimal(coupon_rate)
    ytm = safe_decimal(ytm)
    face_value = safe_decimal(face_value) or DEFAULT_FACE_VALUE

    if coupon_rate is None or ytm is None or maturity_date is None:
        return None

    if face_value <= ZERO:
        return None

    coupon_frequency = normalize_coupon_frequency(coupon_frequency)
    cash_flow_times = build_cash_flow_times(
        maturity_date=maturity_date,
        quote_date=quote_date,
        coupon_frequency=coupon_frequency,
    )

    if not cash_flow_times:
        return None

    periodic_yield = (ytm / HUNDRED) / Decimal(coupon_frequency)

    if ONE + periodic_yield <= ZERO:
        return None

    coupon_payment = (
        face_value
        * (coupon_rate / HUNDRED)
        / Decimal(coupon_frequency)
    )

    present_value_sum = ZERO
    weighted_time_sum = ZERO

    for index, time_in_years in enumerate(cash_flow_times, start=1):
        cash_flow = coupon_payment

        if index == len(cash_flow_times):
            cash_flow += face_value

        exponent = time_in_years * Decimal(coupon_frequency)
        present_value = cash_flow / ((ONE + periodic_yield) ** exponent)

        present_value_sum += present_value
        weighted_time_sum += time_in_years * present_value

    if present_value_sum <= ZERO:
        return None

    macaulay_duration = weighted_time_sum / present_value_sum
    modified_duration = macaulay_duration / (ONE + periodic_yield)

    return quantize_decimal(modified_duration, "0.000001")


def calculate_basic_bond_metrics(
    market_price: Any,
    coupon_rate: Any,
    maturity_date: date | None,
    ytm: Any = None,
    duration: Any = None,
    quote_date: date | None = None,
    face_value: Any = DEFAULT_FACE_VALUE,
    coupon_frequency: Any = DEFAULT_COUPON_FREQUENCY,
) -> dict[str, Any]:
    """
    Fill missing basic bond metrics using backend calculations.

    Args:
        market_price: Market price per face value.
        coupon_rate: Annual coupon rate as percentage.
        maturity_date: Maturity date.
        ytm: Optional existing YTM.
        duration: Optional existing modified duration.
        quote_date: Valuation date.
        face_value: Face value.
        coupon_frequency: Coupon payments per year.

    Returns:
        Dictionary with calculated metrics and traceability metadata.
    """
    calculated_fields: list[str] = []
    missing_required_fields: list[str] = []
    calculation_notes: list[str] = []

    market_price_decimal = safe_decimal(market_price)
    coupon_rate_decimal = safe_decimal(coupon_rate)
    ytm_decimal = safe_decimal(ytm)
    duration_decimal = safe_decimal(duration)
    face_value_decimal = safe_decimal(face_value) or DEFAULT_FACE_VALUE
    coupon_frequency_integer = normalize_coupon_frequency(coupon_frequency)

    if market_price_decimal is None:
        missing_required_fields.append("market_price")

    if coupon_rate_decimal is None:
        missing_required_fields.append("coupon_rate")

    if maturity_date is None:
        missing_required_fields.append("maturity_date")

    if missing_required_fields:
        return {
            "ytm": ytm_decimal,
            "duration": duration_decimal,
            "calculated_fields": calculated_fields,
            "missing_required_fields": missing_required_fields,
            "calculation_notes": (
                "Cannot calculate YTM/duration because required fields are missing: "
                + ", ".join(missing_required_fields)
                + "."
            ),
            "can_calculate": False,
        }

    if ytm_decimal is None:
        ytm_decimal = calculate_ytm(
            market_price=market_price_decimal,
            coupon_rate=coupon_rate_decimal,
            maturity_date=maturity_date,
            quote_date=quote_date,
            face_value=face_value_decimal,
            coupon_frequency=coupon_frequency_integer,
        )

        if ytm_decimal is not None:
            calculated_fields.append("ytm")
            calculation_notes.append(
                "YTM was calculated by the backend from market price, coupon and maturity."
            )

    if duration_decimal is None and ytm_decimal is not None:
        duration_decimal = calculate_modified_duration(
            coupon_rate=coupon_rate_decimal,
            maturity_date=maturity_date,
            ytm=ytm_decimal,
            quote_date=quote_date,
            face_value=face_value_decimal,
            coupon_frequency=coupon_frequency_integer,
        )

        if duration_decimal is not None:
            calculated_fields.append("duration")
            calculation_notes.append(
                "Modified duration was calculated by the backend from cash flows and YTM."
            )

    return {
        "ytm": quantize_decimal(ytm_decimal, "0.00001"),
        "duration": quantize_decimal(duration_decimal, "0.000001"),
        "calculated_fields": calculated_fields,
        "missing_required_fields": missing_required_fields,
        "calculation_notes": " ".join(calculation_notes),
        "can_calculate": True,
    }
