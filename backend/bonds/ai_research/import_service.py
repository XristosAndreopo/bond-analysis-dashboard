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
from bonds.analytics.bond_math import calculate_basic_bond_metrics
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
    coupon_rate = _parse_decimal(item.get("coupon_rate"))
    market_price = _parse_decimal(item.get("market_price"))
    coupon_frequency = _parse_integer(item.get("coupon_frequency"), default=1)
    ytm = _parse_decimal(item.get("ytm"))
    duration = _parse_decimal(item.get("duration"))

    if coupon_rate is None:
        raise AIResearchImportError(
            f"{isin} skipped: coupon_rate is required for backend YTM/duration calculation."
        )

    if market_price is None:
        raise AIResearchImportError(
            f"{isin} skipped: market_price is required for backend YTM/duration calculation."
        )

    metric_result = calculate_basic_bond_metrics(
        market_price=market_price,
        coupon_rate=coupon_rate,
        maturity_date=maturity_date,
        ytm=ytm,
        duration=duration,
        quote_date=timezone.localdate(),
        face_value=Decimal("100.0000"),
        coupon_frequency=coupon_frequency,
    )

    if metric_result["ytm"] is None:
        raise AIResearchImportError(
            f"{isin} skipped: YTM is missing and could not be calculated by the backend."
        )

    if metric_result["duration"] is None:
        raise AIResearchImportError(
            f"{isin} skipped: duration is missing and could not be calculated by the backend."
        )

    missing_fields = _remove_backend_calculated_fields_from_missing_fields(
        missing_fields=_normalize_list(item.get("missing_fields")),
        calculated_fields=metric_result["calculated_fields"],
    )
    research_payload = _build_research_payload_with_backend_calculations(
        item=item,
        metric_result=metric_result,
    )
    research_notes = _build_research_notes_with_backend_calculations(
        research_notes=_normalize_text(item.get("research_notes")),
        metric_result=metric_result,
    )

    defaults = {
        "discovery_run": discovery_run,
        "name": _truncate(_normalize_text(item.get("name")), 255),
        "issuer": _truncate(_normalize_text(item.get("issuer")), 255),
        "country": _normalize_country_code(item.get("country")),
        "currency": _normalize_currency(item.get("currency")),
        "coupon_rate": coupon_rate,
        "maturity_date": maturity_date,
        "credit_rating": credit_rating,
        "rating_source": _truncate(_normalize_text(item.get("rating_source")), 100),
        "market_price": market_price,
        "ytm": metric_result["ytm"],
        "duration": metric_result["duration"],
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
        "missing_fields": missing_fields,
        "research_payload": research_payload,
        "ai_summary": _truncate(research_notes, 5000),
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

    raw_market_price = _parse_decimal(item.get("market_price"))
    market_price = raw_market_price
    market_price_fallback_note = ""
    market_price_fallback_payload: dict[str, Any] | None = None

    if market_price is None:
        fallback_market_data = _get_latest_market_data_with_price(bond)

        if fallback_market_data is None:
            raise AIResearchImportError(
                f"{isin} skipped: market_price is required for BondMarketData "
                "and no previous stored market price exists."
            )

        market_price = fallback_market_data.market_price
        market_price_fallback_note = (
            "Market price was not verified in this AI refresh. "
            f"The previous stored market price {fallback_market_data.market_price} "
            f"from {fallback_market_data.quote_date} / "
            f"{fallback_market_data.source} was carried forward. "
            "Treat this record as NEEDS_REVIEW."
        )
        market_price_fallback_payload = {
            "used": True,
            "reason": "market_price missing from current AI refresh",
            "fallback_market_data_id": fallback_market_data.id,
            "fallback_quote_date": fallback_market_data.quote_date.isoformat(),
            "fallback_source": fallback_market_data.source,
            "fallback_market_price": str(fallback_market_data.market_price),
        }

    ai_reported_quote_date = _parse_date(item.get("quote_date"))
    quote_date = timezone.localdate()

    # Use a stable internal source and a stable daily import date for AI market
    # refresh records.
    #
    # BondMarketData has a uniqueness rule on (bond, quote_date, source).
    # If we use the AI-selected primary_source_name or AI-reported quote_date
    # directly, the same daily refresh can create duplicate rows whenever the
    # AI finds a different public source or a different source quote date on
    # the next run.
    #
    # The real public source and AI-reported quote date are still preserved in
    # source_url, research_payload, and notes.
    source = AI_RESEARCH_SOURCE

    _update_bond_identity_from_market_item(
        bond=bond,
        item=item,
    )

    metric_result = calculate_basic_bond_metrics(
        market_price=market_price,
        coupon_rate=bond.annual_coupon_rate,
        maturity_date=bond.maturity_date,
        ytm=_parse_decimal(item.get("ytm")),
        duration=None,
        quote_date=quote_date,
        face_value=bond.face_value,
        coupon_frequency=bond.coupon_frequency,
    )

    if metric_result["ytm"] is None:
        raise AIResearchImportError(
            f"{isin} skipped: YTM is missing and could not be calculated by the backend."
        )

    missing_fields = _remove_backend_calculated_fields_from_missing_fields(
        missing_fields=_normalize_list(item.get("missing_fields")),
        calculated_fields=metric_result["calculated_fields"],
    )

    if raw_market_price is None:
        missing_fields = _append_unique_missing_field(
            missing_fields=missing_fields,
            field_name="market_price",
        )

    research_payload = _build_research_payload_with_backend_calculations(
        item=item,
        metric_result=metric_result,
    )

    research_payload["_ai_market_refresh_import"] = {
        "stored_quote_date": quote_date.isoformat(),
        "ai_reported_quote_date": (
            ai_reported_quote_date.isoformat()
            if ai_reported_quote_date is not None
            else None
        ),
        "stored_source": source,
        "ai_primary_source_name": _normalize_text(item.get("primary_source_name")),
        "reason": (
            "AI market refresh records use a stable daily import quote_date "
            "and stable internal source to prevent duplicate rows for the same "
            "bond on repeated refreshes within the same day."
        ),
    }

    if market_price_fallback_payload is not None:
        research_payload["_market_price_fallback"] = market_price_fallback_payload

    notes = _build_research_notes_with_backend_calculations(
        research_notes=_normalize_text(item.get("research_notes")),
        metric_result=metric_result,
    )
    notes = _append_note(
        notes,
        _build_stable_ai_market_refresh_note(
            stored_quote_date=quote_date,
            ai_reported_quote_date=ai_reported_quote_date,
            source=source,
        ),
    )
    notes = _append_note(notes, market_price_fallback_note)

    market_data, created = BondMarketData.objects.update_or_create(
        bond=bond,
        quote_date=quote_date,
        source=source,
        defaults={
            "market_price": market_price,
            "market_required_return": _parse_decimal(
                item.get("market_required_return")
            ),
            "ytm": metric_result["ytm"],
            "bid_price": _parse_decimal(item.get("bid_price")),
            "ask_price": _parse_decimal(item.get("ask_price")),
            "source_url": _truncate(
                _normalize_text(item.get("primary_source_url")),
                500,
            ),
            "data_origin": DataOrigin.AI_RESEARCH,
            "is_manual": False,
            "retrieved_at": _parse_datetime(item.get("retrieved_at")),
            "confidence": (
                ResearchConfidence.LOW
                if raw_market_price is None
                else _normalize_confidence(item.get("confidence"))
            ),
            "needs_review": bool(item.get("needs_review", True)) or raw_market_price is None,
            "review_status": (
                ReviewStatus.NEEDS_REVIEW
                if raw_market_price is None
                else _normalize_review_status(item.get("review_status"))
            ),
            "missing_fields": missing_fields,
            "research_payload": research_payload,
            "notes": notes,
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


def _get_latest_market_data_with_price(bond: Bond) -> BondMarketData | None:
    """
    Return the latest existing market data row with a stored market price.

    This is used only as a transparent fallback for market refresh runs where
    the AI can verify yield or identity data but cannot verify a fresh public
    price. The carried-forward price is clearly marked in notes, missing_fields
    and research_payload.
    """
    return (
        bond.market_data.exclude(market_price__isnull=True)
        .order_by("-quote_date", "-created_at")
        .first()
    )


def _append_unique_missing_field(
    missing_fields: list[str],
    field_name: str,
) -> list[str]:
    """
    Append a missing field once while preserving the existing order.
    """
    normalized_existing = {field.lower() for field in missing_fields}

    if field_name.lower() in normalized_existing:
        return missing_fields

    return [*missing_fields, field_name]


def _append_note(base_note: str, extra_note: str) -> str:
    """
    Append an extra note when it exists.
    """
    base_note = base_note.strip()
    extra_note = extra_note.strip()

    if not extra_note:
        return base_note

    if not base_note:
        return extra_note

    return f"{base_note} {extra_note}"


def _build_stable_ai_market_refresh_note(
    stored_quote_date: date,
    ai_reported_quote_date: date | None,
    source: str,
) -> str:
    """
    Build a note explaining the stable AI market refresh storage policy.

    AI market refresh records are stored under a stable daily import date and
    stable internal source to avoid duplicate rows when the AI finds different
    public quote dates or source names on repeated runs.
    """
    ai_quote_date_text = (
        ai_reported_quote_date.isoformat()
        if ai_reported_quote_date is not None
        else "not provided"
    )

    return (
        "AI market refresh storage policy: this record is stored with "
        f"quote_date {stored_quote_date.isoformat()} and source {source}. "
        f"The AI-reported source quote date was {ai_quote_date_text}. "
        "The original AI-reported source details remain in research_payload "
        "and source_url."
    )


def _parse_integer(value: Any, default: int = 1) -> int:
    """
    Parse an optional integer value safely.

    Args:
        value: Raw integer-like value.
        default: Fallback value.

    Returns:
        Parsed integer or default.
    """
    if value is None or value == "":
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _remove_backend_calculated_fields_from_missing_fields(
    missing_fields: list[str],
    calculated_fields: list[str],
) -> list[str]:
    """
    Remove fields from missing_fields when the backend calculated them.

    Args:
        missing_fields: Original missing fields from AI research.
        calculated_fields: Fields calculated by the backend.

    Returns:
        Cleaned missing fields.
    """
    calculated_set = {field.lower() for field in calculated_fields}

    return [
        field
        for field in missing_fields
        if field.lower() not in calculated_set
    ]


def _build_research_payload_with_backend_calculations(
    item: dict[str, Any],
    metric_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Attach backend calculation metadata to the raw research payload.

    Args:
        item: Original AI item.
        metric_result: Backend calculation result.

    Returns:
        Payload with _backend_calculations metadata.
    """
    payload = dict(item)
    payload["_backend_calculations"] = {
        "calculated_fields": metric_result["calculated_fields"],
        "missing_required_fields": metric_result["missing_required_fields"],
        "calculation_notes": metric_result["calculation_notes"],
        "ytm": str(metric_result["ytm"]) if metric_result["ytm"] is not None else None,
        "duration": (
            str(metric_result["duration"])
            if metric_result["duration"] is not None
            else None
        ),
    }

    return payload


def _build_research_notes_with_backend_calculations(
    research_notes: str,
    metric_result: dict[str, Any],
) -> str:
    """
    Append backend calculation notes to AI research notes.

    Args:
        research_notes: Original research notes.
        metric_result: Backend calculation result.

    Returns:
        Combined notes string.
    """
    notes = research_notes.strip()

    if metric_result["calculation_notes"]:
        if notes:
            notes += " "

        notes += metric_result["calculation_notes"]

    return notes


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




