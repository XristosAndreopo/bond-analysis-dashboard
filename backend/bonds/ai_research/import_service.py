"""
Import service for AI-researched bond data.

This module imports structured JSON returned by the AI Research Agent.

Important rules:
- AI-researched data is not treated as an official live market feed.
- Every imported record keeps source, source URL, retrieved timestamp,
  confidence, review status, missing fields, and raw payload.
- Missing market data is not guessed.
- Discovery research creates/updates BondCandidate records.
- Market refresh research creates/updates BondMarketData records only for
  bonds that already exist in the application.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from django.utils import timezone

from bonds.ai_research.schemas import (
    validate_discovery_research_result,
    validate_market_research_result,
)
from bonds.discovery.rating_utils import RatingError, normalize_rating
from bonds.models import (
    Bond,
    BondCandidate,
    BondMarketData,
    DataOrigin,
    DiscoveryRun,
    ResearchConfidence,
    ReviewStatus,
)
from portfolios.models import UserBond


AI_RESEARCH_SOURCE = "ai_research_agent"

COUNTRY_CODE_MAP = {
    "GREECE": "GR",
    "HELLAS": "GR",
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "USA": "US",
    "U.S.": "US",
    "US": "US",
    "GR": "GR",
}


class AIResearchImportError(Exception):
    """
    Raised when AI research JSON cannot be imported safely.
    """


@transaction.atomic
def import_discovery_research_result(user, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Import AI discovery JSON into BondCandidate records.

    Args:
        user: Authenticated Django user.
        payload: Parsed JSON returned by the AI Research Agent.

    Returns:
        Import summary dictionary.

    Raises:
        AIResearchImportError: If the payload fails validation or import fails.
    """
    validation_errors = validate_discovery_research_result(payload)

    if validation_errors:
        raise AIResearchImportError(_join_errors(validation_errors))

    filters = payload.get("filters") or {}
    countries = _normalize_string_list(filters.get("countries"))
    currencies = _normalize_string_list(filters.get("currencies"))

    discovery_run = DiscoveryRun.objects.create(
        user=user,
        source=AI_RESEARCH_SOURCE,
        min_rating=filters.get("minimum_rating") or "",
        currencies=currencies,
        countries=countries,
    )
    discovery_run.mark_running()

    total_found = len(payload.get("items") or [])
    total_created = 0
    total_updated = 0
    total_skipped = 0
    errors: list[str] = []

    try:
        for item in payload.get("items") or []:
            try:
                import_result = _import_single_discovery_item(
                    user=user,
                    discovery_run=discovery_run,
                    item=item,
                )
            except AIResearchImportError as exc:
                total_skipped += 1
                errors.append(str(exc))
                continue

            if import_result == "created":
                total_created += 1
            elif import_result == "updated":
                total_updated += 1
            else:
                total_skipped += 1

        discovery_run.mark_completed(
            total_found=total_found,
            total_saved=total_created + total_updated,
            total_skipped=total_skipped,
        )

        return {
            "discovery_run_id": discovery_run.id,
            "total_found": total_found,
            "total_created": total_created,
            "total_updated": total_updated,
            "total_skipped": total_skipped,
            "errors": errors,
        }

    except Exception as exc:
        discovery_run.mark_failed(str(exc))
        raise AIResearchImportError(str(exc)) from exc


@transaction.atomic
def import_market_research_result(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Import AI market refresh JSON into BondMarketData records.

    This function updates market data only for bonds that already exist in the
    application. It does not create Bond master records from market refresh
    payloads.

    Args:
        payload: Parsed JSON returned by the AI Research Agent.

    Returns:
        Import summary dictionary.

    Raises:
        AIResearchImportError: If the payload fails validation or import fails.
    """
    validation_errors = validate_market_research_result(payload)

    if validation_errors:
        raise AIResearchImportError(_join_errors(validation_errors))

    total_found = len(payload.get("items") or [])
    total_created = 0
    total_updated = 0
    total_skipped = 0
    errors: list[str] = []

    for item in payload.get("items") or []:
        try:
            import_result = _import_single_market_item(item)
        except AIResearchImportError as exc:
            total_skipped += 1
            errors.append(str(exc))
            continue

        if import_result == "created":
            total_created += 1
        elif import_result == "updated":
            total_updated += 1
        else:
            total_skipped += 1

    return {
        "total_found": total_found,
        "total_created": total_created,
        "total_updated": total_updated,
        "total_skipped": total_skipped,
        "errors": errors,
    }


def _import_single_discovery_item(
    user,
    discovery_run: DiscoveryRun,
    item: dict[str, Any],
) -> str:
    """
    Import one AI-researched discovery item.

    Returns:
        "created", "updated", or "skipped".
    """
    isin = _normalize_isin(item.get("isin"))

    if not isin:
        raise AIResearchImportError("Discovery item skipped: missing ISIN.")

    if _is_active_for_user(user=user, isin=isin):
        return "skipped"

    existing_candidate = BondCandidate.objects.filter(
        user=user,
        isin=isin,
    ).first()

    if _should_keep_existing_candidate(existing_candidate):
        return "skipped"

    maturity_date = _parse_date(item.get("maturity_date"))

    if maturity_date is None:
        raise AIResearchImportError(
            f"{isin} skipped: maturity_date is required for BondCandidate."
        )

    if maturity_date <= timezone.localdate():
        return "skipped"

    credit_rating = _normalize_credit_rating(item.get("credit_rating"))

    defaults = {
        "discovery_run": discovery_run,
        "name": _truncate(_normalize_text(item.get("name")), 255),
        "issuer": _truncate(_normalize_text(item.get("issuer")), 255),
        "country": _normalize_country_code(item.get("country")),
        "currency": _normalize_currency(item.get("currency")),
        "coupon_rate": _parse_decimal(item.get("coupon_rate")),
        "maturity_date": maturity_date,
        "credit_rating": credit_rating,
        "rating_source": _truncate(_normalize_text(item.get("rating_source")), 100),
        "market_price": _parse_decimal(item.get("market_price")),
        "ytm": _parse_decimal(item.get("ytm")),
        "duration": _parse_decimal(item.get("duration")),
        "source": _truncate(
            _normalize_text(item.get("primary_source_name")) or AI_RESEARCH_SOURCE,
            100,
        ),
        "source_url": _truncate(_normalize_text(item.get("primary_source_url")), 500),
        "data_origin": DataOrigin.AI_RESEARCH,
        "retrieved_at": _parse_datetime(item.get("retrieved_at")),
        "confidence": _normalize_confidence(item.get("confidence")),
        "needs_review": bool(item.get("needs_review", True)),
        "review_status": _normalize_review_status(item.get("review_status")),
        "missing_fields": _normalize_list(item.get("missing_fields")),
        "research_payload": item,
        "ai_summary": _truncate(_normalize_text(item.get("research_notes")), 5000),
        "ai_reasoning": "",
        "status": BondCandidate.Status.NEW,
    }

    candidate, created = BondCandidate.objects.update_or_create(
        user=user,
        isin=isin,
        defaults=defaults,
    )

    return "created" if created else "updated"


def _import_single_market_item(item: dict[str, Any]) -> str:
    """
    Import one AI-researched market refresh item.

    Returns:
        "created", "updated", or "skipped".
    """
    isin = _normalize_isin(item.get("isin"))

    if not isin:
        raise AIResearchImportError("Market item skipped: missing ISIN.")

    bond = Bond.objects.filter(isin=isin).first()

    if bond is None:
        raise AIResearchImportError(
            f"{isin} skipped: bond does not exist in the application."
        )

    market_price = _parse_decimal(item.get("market_price"))

    if market_price is None:
        raise AIResearchImportError(
            f"{isin} skipped: market_price is required for BondMarketData."
        )

    quote_date = _parse_date(item.get("quote_date")) or timezone.localdate()
    source = _truncate(
        _normalize_text(item.get("primary_source_name")) or AI_RESEARCH_SOURCE,
        100,
    )

    _update_bond_identity_from_market_item(
        bond=bond,
        item=item,
    )

    market_data, created = BondMarketData.objects.update_or_create(
        bond=bond,
        quote_date=quote_date,
        source=source,
        defaults={
            "market_price": market_price,
            "market_required_return": _parse_decimal(
                item.get("market_required_return")
            ),
            "ytm": _parse_decimal(item.get("ytm")),
            "bid_price": _parse_decimal(item.get("bid_price")),
            "ask_price": _parse_decimal(item.get("ask_price")),
            "source_url": _truncate(
                _normalize_text(item.get("primary_source_url")),
                500,
            ),
            "data_origin": DataOrigin.AI_RESEARCH,
            "is_manual": False,
            "retrieved_at": _parse_datetime(item.get("retrieved_at")),
            "confidence": _normalize_confidence(item.get("confidence")),
            "needs_review": bool(item.get("needs_review", True)),
            "review_status": _normalize_review_status(item.get("review_status")),
            "missing_fields": _normalize_list(item.get("missing_fields")),
            "research_payload": item,
            "notes": _normalize_text(item.get("research_notes")),
        },
    )

    return "created" if created else "updated"


def _update_bond_identity_from_market_item(
    bond: Bond,
    item: dict[str, Any],
) -> None:
    """
    Update safe Bond identity fields from market refresh data.

    This function only updates fields that are safe to refresh from research:
    - credit_rating, if provided
    - issuer, only if the existing issuer is blank
    - name, only if the existing name is blank
    """
    update_fields: list[str] = []

    credit_rating = _normalize_credit_rating(item.get("credit_rating"))

    if credit_rating and credit_rating != bond.credit_rating:
        bond.credit_rating = credit_rating
        update_fields.append("credit_rating")

    issuer = _normalize_text(item.get("issuer"))

    if issuer and not bond.issuer:
        bond.issuer = _truncate(issuer, 255)
        update_fields.append("issuer")

    name = _normalize_text(item.get("name"))

    if name and not bond.name:
        bond.name = _truncate(name, 255)
        update_fields.append("name")

    if update_fields:
        update_fields.append("updated_at")
        bond.save(update_fields=update_fields)


def _is_active_for_user(user, isin: str) -> bool:
    """
    Check whether the ISIN already exists in user's active holdings.
    """
    return UserBond.objects.filter(
        user=user,
        bond__isin=isin,
        is_active=True,
    ).exists()


def _should_keep_existing_candidate(candidate: BondCandidate | None) -> bool:
    """
    Return True when an existing candidate should not be overwritten.
    """
    if candidate is None:
        return False

    return candidate.status in [
        BondCandidate.Status.ADDED_TO_WATCHLIST,
        BondCandidate.Status.IGNORED,
    ]


def _normalize_text(value: Any) -> str:
    """
    Convert a value to clean text.
    """
    if value is None:
        return ""

    return str(value).strip()


def _normalize_isin(value: Any) -> str:
    """
    Normalize an ISIN value.
    """
    return _normalize_text(value).upper()


def _normalize_currency(value: Any) -> str:
    """
    Normalize a currency code.

    Defaults to EUR only when the value is missing. This is a defensive fallback
    because BondCandidate.currency is required by the current model.
    """
    currency = _normalize_text(value).upper()

    if len(currency) == 3:
        return currency

    return "EUR"


def _normalize_country_code(value: Any) -> str:
    """
    Normalize a country value to a 2-letter code when possible.
    """
    country = _normalize_text(value).upper()

    if not country:
        return ""

    if country in COUNTRY_CODE_MAP:
        return COUNTRY_CODE_MAP[country]

    if len(country) == 2:
        return country

    return ""


def _normalize_credit_rating(value: Any) -> str:
    """
    Normalize a credit rating when possible.

    Invalid or missing ratings are kept empty instead of guessed.
    """
    rating = _normalize_text(value)

    if not rating:
        return ""

    try:
        return normalize_rating(rating)
    except RatingError:
        return rating.upper()


def _normalize_confidence(value: Any) -> str:
    """
    Normalize confidence enum.
    """
    confidence = _normalize_text(value).upper()

    if confidence in ResearchConfidence.values:
        return confidence

    return ResearchConfidence.LOW


def _normalize_review_status(value: Any) -> str:
    """
    Normalize review status enum.
    """
    review_status = _normalize_text(value).upper()

    if review_status in ReviewStatus.values:
        return review_status

    return ReviewStatus.NEEDS_REVIEW


def _normalize_list(value: Any) -> list[str]:
    """
    Normalize list-like values into a list of strings.
    """
    if not value:
        return []

    if not isinstance(value, list):
        return [_normalize_text(value)]

    return [_normalize_text(item) for item in value if _normalize_text(item)]


def _normalize_string_list(value: Any) -> list[str]:
    """
    Normalize a list of strings.
    """
    return [item.upper() for item in _normalize_list(value)]


def _parse_decimal(value: Any) -> Decimal | None:
    """
    Parse optional decimal values.

    Accepts numbers and numeric strings. Percentage symbols and commas are
    removed defensively because web-researched data can include formatting.
    """
    if value is None or value == "":
        return None

    normalized_value = str(value).strip().replace("%", "").replace(",", "")

    if not normalized_value:
        return None

    try:
        return Decimal(normalized_value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    """
    Parse optional ISO date.
    """
    if value is None or value == "":
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    """
    Parse optional ISO datetime.

    Accepts a trailing Z by converting it to +00:00.
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        parsed_datetime = value
    else:
        normalized_value = str(value).strip().replace("Z", "+00:00")

        try:
            parsed_datetime = datetime.fromisoformat(normalized_value)
        except ValueError:
            return None

    if timezone.is_naive(parsed_datetime):
        return timezone.make_aware(parsed_datetime)

    return parsed_datetime


def _truncate(value: str, max_length: int) -> str:
    """
    Truncate text to a model-safe length.
    """
    if not value:
        return ""

    return value[:max_length]


def _join_errors(errors: list[str]) -> str:
    """
    Join validation errors into a readable message.
    """
    return " | ".join(errors)