"""
Preliminary signal logic for discovered bond candidates.

This module provides a lightweight, deterministic preliminary analysis for
BondCandidate records before they are added to the user's Watchlist.

Important:
    This is not the full Watchlist or Portfolio analysis.

Discovery preview uses only candidate-level data:
    - credit rating
    - YTM
    - duration
    - maturity
    - currency
    - market price

The final analytical signal is produced only after the candidate is added to
Watchlist or Portfolio.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from bonds.discovery.rating_utils import RatingError, get_rating_score


@dataclass(frozen=True)
class CandidatePreview:
    """
    Preliminary preview result for a discovered bond candidate.
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
    "BUY_WITH_CAUTION": "Υποψήφιο με προσοχή",
    "DO_NOT_BUY_WAIT": "Περίμενε / έλεγξε",
    "REVIEW": "Χρειάζεται έλεγχο",
}


def evaluate_candidate_preview(candidate):
    """
    Evaluate a BondCandidate and return a deterministic preliminary signal.

    Args:
        candidate: BondCandidate instance.

    Returns:
        CandidatePreview instance.
    """
    rating_score = safe_rating_score(candidate.credit_rating)
    duration = safe_decimal(candidate.duration)
    ytm = safe_decimal(candidate.ytm)

    risk_points = 0

    risk_points += calculate_rating_points(rating_score)
    risk_points += calculate_duration_points(duration)
    risk_points += calculate_ytm_points(ytm)

    preview_risk_level = calculate_risk_level(risk_points)
    preview_signal = calculate_preview_signal(
        rating_score=rating_score,
        duration=duration,
        ytm=ytm,
        preview_risk_level=preview_risk_level,
    )

    return CandidatePreview(
        preview_risk_level=preview_risk_level,
        preview_risk_label=RISK_LABELS.get(
            preview_risk_level,
            preview_risk_level,
        ),
        preview_signal=preview_signal,
        preview_signal_label=SIGNAL_LABELS.get(
            preview_signal,
            preview_signal,
        ),
        preview_reasoning=build_short_reasoning(
            candidate=candidate,
            duration=duration,
            ytm=ytm,
        ),
    )


def build_short_reasoning(candidate, duration, ytm):
    """
    Build a short reasoning text for Discover Bonds.

    Args:
        candidate: BondCandidate instance.
        duration: Candidate duration.
        ytm: Candidate YTM.

    Returns:
        str: Short reasoning text.
    """
    rating_text = candidate.credit_rating or "χωρίς rating"
    ytm_text = f"{ytm}%" if ytm is not None else "χωρίς διαθέσιμο YTM"
    duration_text = (
        f"{duration}" if duration is not None else "χωρίς διαθέσιμο duration"
    )

    return (
        "Ένδειξη με βάση τα διαθέσιμα στοιχεία του candidate: "
        f"rating {rating_text}, YTM {ytm_text}, duration {duration_text}."
    )


def safe_decimal(value):
    """
    Convert a value to Decimal safely.
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
    """
    if not rating:
        return None

    try:
        return get_rating_score(rating)
    except RatingError:
        return None


def calculate_rating_points(rating_score):
    """
    Calculate preliminary risk points from credit rating.

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
    Calculate preliminary risk points from duration.
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
    Calculate preliminary risk points from YTM.
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
    Convert preliminary risk points to a RiskBadge-compatible risk level.
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
    Convert preliminary inputs to a SignalBadge-compatible signal.
    """
    if rating_score is None or ytm is None:
        return "REVIEW"

    has_good_rating = rating_score >= 70
    has_investment_grade_rating = rating_score >= 55
    has_reasonable_duration = duration is None or duration <= Decimal("7.00")
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


