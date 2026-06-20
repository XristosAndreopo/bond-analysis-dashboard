"""
Preview signal logic for discovered bond candidates.

This module provides a lightweight, deterministic preview analysis for
BondCandidate records before they are added to the user's Watchlist.

Important:
    This is not the full portfolio/watchlist analysis.

Full analysis requires:
    - UserBond
    - latest BondMarketData
    - cash flow calculations
    - intrinsic value calculation
    - risk score calculation
    - final signal calculation

Discovery preview uses only candidate-level data:
    - credit rating
    - YTM
    - duration
    - maturity
    - currency
    - market price

The goal is to help the user prioritize candidates before adding them to
Watchlist. It is educational/analytical only and not investment advice.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from bonds.discovery.rating_utils import RatingError, get_rating_score


@dataclass(frozen=True)
class CandidatePreview:
    """
    Preview result for a discovered bond candidate.

    Attributes:
        preview_risk_level: Risk level code compatible with RiskBadge.
        preview_risk_label: Human-readable risk label.
        preview_signal: Signal code compatible with SignalBadge CSS.
        preview_signal_label: Human-readable signal label.
        preview_reasoning: Short explanation shown in the UI.
    """

    preview_risk_level: str
    preview_risk_label: str
    preview_signal: str
    preview_signal_label: str
    preview_reasoning: str


RISK_LABELS = {
    "VERY_LOW": "Πολύ χαμηλό",
    "LOW": "Χαμηλό",
    "MEDIUM": "Μεσαίο",
    "HIGH": "Υψηλό",
    "VERY_HIGH": "Πολύ υψηλό",
}

SIGNAL_LABELS = {
    "BUY": "Υποψήφιο για αγορά",
    "BUY_WITH_CAUTION": "Αγορά με προσοχή",
    "DO_NOT_BUY_WAIT": "Περίμενε / Έλεγξε",
    "REVIEW": "Χρειάζεται έλεγχο",
}


def evaluate_candidate_preview(candidate):
    """
    Evaluate a BondCandidate and return a deterministic preview signal.

    Args:
        candidate: BondCandidate instance.

    Returns:
        CandidatePreview instance.

    Notes:
        This function does not write to the database.
        It does not replace the full analytics engine.
    """
    rating_score = safe_rating_score(candidate.credit_rating)
    duration = safe_decimal(candidate.duration)
    ytm = safe_decimal(candidate.ytm)

    risk_points = 0
    reasoning_parts = []

    rating_points = calculate_rating_points(rating_score)
    risk_points += rating_points

    if rating_score is None:
        reasoning_parts.append("Δεν υπάρχει έγκυρη πιστοληπτική αξιολόγηση.")
    elif rating_score >= 85:
        reasoning_parts.append("Πολύ ισχυρό rating.")
    elif rating_score >= 70:
        reasoning_parts.append("Καλό investment-grade rating.")
    elif rating_score >= 55:
        reasoning_parts.append("Οριακό investment-grade rating, θέλει προσοχή.")
    else:
        reasoning_parts.append("Χαμηλό rating για το ζητούμενο προφίλ.")

    duration_points = calculate_duration_points(duration)
    risk_points += duration_points

    if duration is None:
        reasoning_parts.append("Δεν υπάρχει διαθέσιμο duration.")
    elif duration <= Decimal("4.00"):
        reasoning_parts.append("Χαμηλό έως μέτριο duration.")
    elif duration <= Decimal("7.00"):
        reasoning_parts.append("Μέτριο duration.")
    elif duration <= Decimal("10.00"):
        reasoning_parts.append("Υψηλό duration, αυξημένη ευαισθησία σε επιτόκια.")
    else:
        reasoning_parts.append("Πολύ υψηλό duration, σημαντικός επιτοκιακός κίνδυνος.")

    ytm_points = calculate_ytm_points(ytm)
    risk_points += ytm_points

    if ytm is None:
        reasoning_parts.append("Δεν υπάρχει διαθέσιμο YTM.")
    elif ytm < Decimal("2.00"):
        reasoning_parts.append("Χαμηλό YTM σε σχέση με τον κίνδυνο.")
    elif ytm <= Decimal("6.00"):
        reasoning_parts.append("Αποδεκτό YTM για προκαταρκτική αξιολόγηση.")
    elif ytm <= Decimal("8.00"):
        reasoning_parts.append("Υψηλό YTM, χρειάζεται έλεγχος κινδύνου.")
    else:
        reasoning_parts.append("Πολύ υψηλό YTM, πιθανή ένδειξη αυξημένου κινδύνου.")

    preview_risk_level = calculate_risk_level(risk_points)
    preview_signal = calculate_preview_signal(
        rating_score=rating_score,
        duration=duration,
        ytm=ytm,
        preview_risk_level=preview_risk_level,
    )

    return CandidatePreview(
        preview_risk_level=preview_risk_level,
        preview_risk_label=RISK_LABELS.get(preview_risk_level, preview_risk_level),
        preview_signal=preview_signal,
        preview_signal_label=SIGNAL_LABELS.get(preview_signal, preview_signal),
        preview_reasoning=" ".join(reasoning_parts),
    )


def safe_decimal(value):
    """
    Convert a value to Decimal safely.

    Args:
        value: Any decimal-like value.

    Returns:
        Decimal or None.
    """
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def safe_rating_score(rating):
    """
    Convert a rating to a numeric score safely.

    Args:
        rating: Credit rating text.

    Returns:
        Integer score or None.
    """
    if not rating:
        return None

    try:
        return get_rating_score(rating)
    except RatingError:
        return None


def calculate_rating_points(rating_score):
    """
    Calculate risk points from credit rating.

    Lower points are better.
    """
    if rating_score is None:
        return 2

    if rating_score >= 85:
        return 0

    if rating_score >= 70:
        return 1

    if rating_score >= 55:
        return 2

    return 4


def calculate_duration_points(duration):
    """
    Calculate risk points from duration.

    Lower duration usually means lower interest-rate sensitivity.
    """
    if duration is None:
        return 1

    if duration <= Decimal("4.00"):
        return 0

    if duration <= Decimal("7.00"):
        return 1

    if duration <= Decimal("10.00"):
        return 2

    return 3


def calculate_ytm_points(ytm):
    """
    Calculate risk points from YTM.

    Extremely low YTM may not compensate risk.
    Extremely high YTM can indicate elevated market risk.
    """
    if ytm is None:
        return 1

    if ytm < Decimal("2.00"):
        return 2

    if ytm <= Decimal("6.00"):
        return 0

    if ytm <= Decimal("8.00"):
        return 1

    return 2


def calculate_risk_level(risk_points):
    """
    Convert risk points to a RiskBadge-compatible risk level.
    """
    if risk_points <= 1:
        return "LOW"

    if risk_points <= 3:
        return "MEDIUM"

    if risk_points <= 5:
        return "HIGH"

    return "VERY_HIGH"


def calculate_preview_signal(rating_score, duration, ytm, preview_risk_level):
    """
    Convert preview inputs to a SignalBadge-compatible signal.

    Returns:
        BUY, BUY_WITH_CAUTION, DO_NOT_BUY_WAIT, or REVIEW.
    """
    if rating_score is None or ytm is None:
        return "REVIEW"

    has_good_rating = rating_score >= 70
    has_investment_grade_rating = rating_score >= 55
    has_reasonable_duration = (
        duration is None or duration <= Decimal("7.00")
    )
    has_acceptable_yield = Decimal("2.00") <= ytm <= Decimal("6.00")

    if (
        preview_risk_level in ["LOW", "MEDIUM"]
        and has_good_rating
        and has_reasonable_duration
        and has_acceptable_yield
    ):
        return "BUY"

    if (
        preview_risk_level in ["LOW", "MEDIUM", "HIGH"]
        and has_investment_grade_rating
        and ytm >= Decimal("2.00")
    ):
        return "BUY_WITH_CAUTION"

    return "DO_NOT_BUY_WAIT"