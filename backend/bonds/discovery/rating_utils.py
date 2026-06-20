"""
Credit rating utility functions for the bond discovery engine.

The discovery MVP uses a simplified S&P/Fitch-style rating scale:

    AAA, AA+, AA, AA-, A+, A, A-, BBB+, BBB, BBB-,
    BB+, BB, BB-, B+, B, B-, CCC+, CCC, CCC-, CC, C, D

The rating engine is intentionally rule-based. It does not use AI and it does
not infer missing ratings.

Important:
    Moody's-style ratings such as Aaa, Aa1, Baa3 are not converted here.
    If Moody's support is needed later, add an explicit mapping table instead
    of guessing.
"""

from dataclasses import dataclass


INVESTMENT_GRADE_MIN_RATING = "BBB-"


class RatingError(ValueError):
    """
    Raised when a credit rating cannot be normalized or compared.
    """


@dataclass(frozen=True)
class RatingComparisonResult:
    """
    Structured result for rating comparisons.

    Attributes:
        rating: Normalized candidate rating.
        minimum_rating: Normalized minimum accepted rating.
        rating_score: Numeric score for the candidate rating.
        minimum_score: Numeric score for the minimum rating.
        passes: True when rating is equal to or better than minimum_rating.
    """

    rating: str
    minimum_rating: str
    rating_score: int
    minimum_score: int
    passes: bool


# Higher score means better credit quality.
RATING_SCORES = {
    "AAA": 100,
    "AA+": 95,
    "AA": 90,
    "AA-": 85,
    "A+": 80,
    "A": 75,
    "A-": 70,
    "BBB+": 65,
    "BBB": 60,
    "BBB-": 55,
    "BB+": 50,
    "BB": 45,
    "BB-": 40,
    "B+": 35,
    "B": 30,
    "B-": 25,
    "CCC+": 20,
    "CCC": 18,
    "CCC-": 16,
    "CC": 12,
    "C": 8,
    "D": 0,
}


def normalize_rating(rating):
    """
    Normalize a credit rating string.

    Args:
        rating: Raw rating value.

    Returns:
        Normalized rating string.

    Raises:
        RatingError: If rating is empty or unsupported.
    """
    if rating is None:
        raise RatingError("Credit rating is required.")

    normalized_rating = str(rating).upper().strip()

    if not normalized_rating:
        raise RatingError("Credit rating is required.")

    # Remove common whitespace variants.
    normalized_rating = normalized_rating.replace(" ", "")

    if normalized_rating not in RATING_SCORES:
        raise RatingError(f"Unsupported credit rating: {rating}")

    return normalized_rating


def get_rating_score(rating):
    """
    Return the numeric score for a credit rating.

    Higher score means better credit quality.

    Args:
        rating: Raw or normalized rating.

    Returns:
        Integer rating score.

    Raises:
        RatingError: If rating is unsupported.
    """
    normalized_rating = normalize_rating(rating)

    return RATING_SCORES[normalized_rating]


def compare_rating(rating, minimum_rating=INVESTMENT_GRADE_MIN_RATING):
    """
    Compare a rating against a minimum accepted rating.

    Args:
        rating: Candidate credit rating.
        minimum_rating: Minimum accepted credit rating.

    Returns:
        RatingComparisonResult.
    """
    normalized_rating = normalize_rating(rating)
    normalized_minimum_rating = normalize_rating(minimum_rating)

    rating_score = get_rating_score(normalized_rating)
    minimum_score = get_rating_score(normalized_minimum_rating)

    return RatingComparisonResult(
        rating=normalized_rating,
        minimum_rating=normalized_minimum_rating,
        rating_score=rating_score,
        minimum_score=minimum_score,
        passes=rating_score >= minimum_score,
    )


def is_rating_at_least(rating, minimum_rating=INVESTMENT_GRADE_MIN_RATING):
    """
    Check whether a rating is equal to or better than a minimum rating.

    Examples:
        is_rating_at_least("A-", "BBB-")      -> True
        is_rating_at_least("BBB-", "BBB-")    -> True
        is_rating_at_least("BB+", "BBB-")     -> False

    Args:
        rating: Candidate credit rating.
        minimum_rating: Minimum accepted credit rating.

    Returns:
        True if rating is equal to or better than minimum_rating.
    """
    return compare_rating(
        rating=rating,
        minimum_rating=minimum_rating,
    ).passes


def is_investment_grade(rating):
    """
    Check whether a rating is investment grade.

    For this MVP, investment grade means BBB- or higher.

    Args:
        rating: Candidate credit rating.

    Returns:
        True if rating is BBB- or higher.
    """
    return is_rating_at_least(
        rating=rating,
        minimum_rating=INVESTMENT_GRADE_MIN_RATING,
    )


def get_supported_ratings():
    """
    Return supported ratings ordered from best to worst.

    Returns:
        List of supported rating strings.
    """
    return sorted(
        RATING_SCORES.keys(),
        key=lambda rating: RATING_SCORES[rating],
        reverse=True,
    )