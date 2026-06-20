"""
Interest rate stress test services.

This module estimates how Portfolio value may change under parallel yield
curve shocks.

The calculation uses the first-order modified duration approximation:

    Estimated Price Change % ≈ - Modified Duration × Yield Change

Example:
    Modified duration = 4.50
    Yield shock = +1.00%

    Estimated price change = -4.50 × 1.00% = -4.50%

Important:
    This is an approximation. It does not include convexity, spread shocks,
    FX shocks, or non-parallel yield curve movements.
"""

from decimal import Decimal

from analytics.portfolio_services import quantize_decimal, safe_decimal


DEFAULT_SCENARIOS = [
    Decimal("-0.0200"),
    Decimal("-0.0100"),
    Decimal("-0.0050"),
    Decimal("0.0050"),
    Decimal("0.0100"),
    Decimal("0.0200"),
]

ZERO = Decimal("0")


def calculate_interest_rate_stress_test(
    portfolio_rows,
    portfolio_base_currency="EUR",
    scenarios=None,
):
    """
    Calculate portfolio-level and position-level interest rate stress test.

    Args:
        portfolio_rows: Rows returned by calculate_portfolio_analytics().
        portfolio_base_currency: Selected base currency.
        scenarios: Optional list of Decimal yield shocks.

    Returns:
        Dictionary with scenario summary, position impacts, and warnings.
    """
    scenarios = scenarios or DEFAULT_SCENARIOS

    normalized_positions = build_stress_positions(
        portfolio_rows=portfolio_rows,
    )

    current_total_value = sum(
        position["current_value"]
        for position in normalized_positions
        if position["is_included"]
    )

    scenario_rows = build_scenario_rows(
        positions=normalized_positions,
        current_total_value=current_total_value,
        scenarios=scenarios,
        portfolio_base_currency=portfolio_base_currency,
    )

    position_rows = build_position_rows(
        positions=normalized_positions,
        scenarios=scenarios,
        portfolio_base_currency=portfolio_base_currency,
    )

    excluded_positions = [
        position
        for position in normalized_positions
        if not position["is_included"]
    ]

    return {
        "portfolio_base_currency": portfolio_base_currency,
        "method": "Modified duration first-order approximation",
        "disclaimer": (
            "Το stress test βασίζεται σε προσέγγιση modified duration. "
            "Δεν περιλαμβάνει convexity, credit spread shocks ή FX shocks."
        ),
        "current_total_value": quantize_decimal(current_total_value, "0.000001"),
        "scenario_rows": scenario_rows,
        "position_rows": position_rows,
        "best_scenario": get_best_scenario(scenario_rows),
        "worst_scenario": get_worst_scenario(scenario_rows),
        "has_excluded_positions": len(excluded_positions) > 0,
        "excluded_positions": [
            {
                "bond_name": position["bond_name"],
                "isin": position["isin"],
                "reason": position["exclusion_reason"],
            }
            for position in excluded_positions
        ],
    }


def build_stress_positions(portfolio_rows):
    """
    Normalize Portfolio rows into stress-test-ready positions.

    Args:
        portfolio_rows: Rows from Portfolio analytics service.

    Returns:
        List of normalized position dictionaries.
    """
    positions = []

    for row in portfolio_rows:
        user_bond = row["user_bond"]
        bond = user_bond.bond
        analysis = user_bond.analyses.order_by(
            "-analysis_date",
            "-created_at",
        ).first()

        converted_value = safe_decimal(row.get("converted_position_value"))
        modified_duration = (
            safe_decimal(analysis.modified_duration)
            if analysis is not None and analysis.modified_duration is not None
            else None
        )

        exclusion_reason = ""

        if row.get("fx_rate_missing"):
            exclusion_reason = "Missing FX rate."
        elif converted_value <= ZERO:
            exclusion_reason = "Position value is zero or missing."
        elif modified_duration is None:
            exclusion_reason = "Modified duration is missing."

        positions.append(
            {
                "user_bond_id": user_bond.id,
                "bond_name": bond.name,
                "isin": bond.isin,
                "currency": bond.currency,
                "current_value": converted_value,
                "modified_duration": modified_duration,
                "risk_score": (
                    safe_decimal(analysis.risk_score)
                    if analysis is not None and analysis.risk_score is not None
                    else None
                ),
                "risk_level": (
                    analysis.risk_level
                    if analysis is not None
                    else ""
                ),
                "final_signal": (
                    analysis.final_signal
                    if analysis is not None
                    else ""
                ),
                "is_included": exclusion_reason == "",
                "exclusion_reason": exclusion_reason,
            }
        )

    return positions


def build_scenario_rows(
    positions,
    current_total_value,
    scenarios,
    portfolio_base_currency,
):
    """
    Build portfolio-level scenario rows.

    Args:
        positions: Normalized positions.
        current_total_value: Included portfolio value.
        scenarios: Yield shock scenarios.
        portfolio_base_currency: Selected base currency.

    Returns:
        List of scenario result dictionaries.
    """
    scenario_rows = []

    for scenario in scenarios:
        total_estimated_value = ZERO
        total_gain_loss = ZERO

        for position in positions:
            if not position["is_included"]:
                continue

            position_result = calculate_position_scenario(
                current_value=position["current_value"],
                modified_duration=position["modified_duration"],
                yield_shock=scenario,
            )

            total_estimated_value += position_result["estimated_value"]
            total_gain_loss += position_result["gain_loss"]

        gain_loss_percent = calculate_ratio(
            numerator=total_gain_loss,
            denominator=current_total_value,
        )

        scenario_rows.append(
            {
                "scenario": quantize_decimal(scenario, "0.000001"),
                "scenario_label": format_scenario_label(scenario),
                "estimated_portfolio_value": quantize_decimal(
                    total_estimated_value,
                    "0.000001",
                ),
                "gain_loss": quantize_decimal(total_gain_loss, "0.000001"),
                "gain_loss_percent": quantize_decimal(
                    gain_loss_percent,
                    "0.000001",
                ),
                "portfolio_base_currency": portfolio_base_currency,
            }
        )

    return scenario_rows


def build_position_rows(positions, scenarios, portfolio_base_currency):
    """
    Build per-position stress-test rows.

    Args:
        positions: Normalized positions.
        scenarios: Yield shock scenarios.
        portfolio_base_currency: Selected base currency.

    Returns:
        List of per-position scenario impact dictionaries.
    """
    position_rows = []

    for position in positions:
        if not position["is_included"]:
            continue

        scenario_impacts = []

        for scenario in scenarios:
            position_result = calculate_position_scenario(
                current_value=position["current_value"],
                modified_duration=position["modified_duration"],
                yield_shock=scenario,
            )

            scenario_impacts.append(
                {
                    "scenario": quantize_decimal(scenario, "0.000001"),
                    "scenario_label": format_scenario_label(scenario),
                    "estimated_value": quantize_decimal(
                        position_result["estimated_value"],
                        "0.000001",
                    ),
                    "gain_loss": quantize_decimal(
                        position_result["gain_loss"],
                        "0.000001",
                    ),
                    "gain_loss_percent": quantize_decimal(
                        position_result["gain_loss_percent"],
                        "0.000001",
                    ),
                }
            )

        position_rows.append(
            {
                "user_bond_id": position["user_bond_id"],
                "bond_name": position["bond_name"],
                "isin": position["isin"],
                "currency": position["currency"],
                "current_value": quantize_decimal(
                    position["current_value"],
                    "0.000001",
                ),
                "modified_duration": quantize_decimal(
                    position["modified_duration"],
                    "0.000001",
                ),
                "risk_score": (
                    quantize_decimal(position["risk_score"], "0.000001")
                    if position["risk_score"] is not None
                    else None
                ),
                "risk_level": position["risk_level"],
                "final_signal": position["final_signal"],
                "portfolio_base_currency": portfolio_base_currency,
                "scenario_impacts": scenario_impacts,
            }
        )

    return position_rows


def calculate_position_scenario(current_value, modified_duration, yield_shock):
    """
    Calculate one position's estimated value under a yield shock.

    Args:
        current_value: Current position value in base currency.
        modified_duration: Modified duration.
        yield_shock: Yield change as decimal, e.g. 0.0100 for +1%.

    Returns:
        Dictionary with estimated value and gain/loss.
    """
    estimated_change_percent = -modified_duration * yield_shock
    gain_loss = current_value * estimated_change_percent
    estimated_value = current_value + gain_loss

    return {
        "estimated_change_percent": estimated_change_percent,
        "estimated_value": estimated_value,
        "gain_loss": gain_loss,
        "gain_loss_percent": estimated_change_percent,
    }


def calculate_ratio(numerator, denominator):
    """
    Safely calculate numerator / denominator.

    Args:
        numerator: Decimal numerator.
        denominator: Decimal denominator.

    Returns:
        Decimal ratio.
    """
    if denominator is None or denominator == ZERO:
        return ZERO

    return numerator / denominator


def get_best_scenario(scenario_rows):
    """
    Return the scenario with the highest gain/loss.
    """
    if not scenario_rows:
        return None

    return max(
        scenario_rows,
        key=lambda row: safe_decimal(row["gain_loss"]),
    )


def get_worst_scenario(scenario_rows):
    """
    Return the scenario with the lowest gain/loss.
    """
    if not scenario_rows:
        return None

    return min(
        scenario_rows,
        key=lambda row: safe_decimal(row["gain_loss"]),
    )


def format_scenario_label(scenario):
    """
    Format scenario as percentage label.

    Args:
        scenario: Decimal scenario, e.g. 0.0100.

    Returns:
        String label, e.g. '+1.00%'.
    """
    percent_value = scenario * Decimal("100")
    sign = "+" if percent_value > ZERO else ""

    return f"{sign}{percent_value:.2f}%"