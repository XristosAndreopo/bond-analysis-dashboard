"""
Bond discovery service.

This module contains the main business logic for discovering candidate bonds
and converting approved candidates into Watchlist items.

The service is intentionally backend-driven:
- providers load raw candidate data
- this service validates and filters data
- this service excludes bonds already in Portfolio or Watchlist
- this service creates BondCandidate records
- this service converts candidates into Watchlist UserBond records

Supported providers are managed by:
    bonds.discovery.providers.provider_registry

The frontend must not invent candidate data. It only displays backend results.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime as django_parse_datetime

from bonds.analytics.bond_math import calculate_basic_bond_metrics
from bonds.discovery.providers.provider_registry import (
    DEFAULT_DISCOVERY_SOURCE,
    ProviderRegistryError,
    get_provider,
)
from bonds.discovery.rating_utils import (
    INVESTMENT_GRADE_MIN_RATING,
    RatingError,
    is_rating_at_least,
    normalize_rating,
)
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


class DiscoveryServiceError(Exception):
    """
    Raised when the discovery service cannot complete the requested action.
    """


class CandidateValidationError(Exception):
    """
    Raised when a raw candidate cannot be normalized safely.
    """


def normalize_text(value):
    """
    Normalize a text value.

    Args:
        value: Any value that should become text.

    Returns:
        str: Normalized text.
    """
    if value is None:
        return ""

    return str(value).strip()


def normalize_isin(value):
    """
    Normalize an ISIN-like value.

    Args:
        value: Raw ISIN.

    Returns:
        str: Uppercase ISIN.
    """
    return normalize_text(value).upper()


def normalize_currency(value):
    """
    Normalize currency code.

    Args:
        value: Raw currency.

    Returns:
        str: Uppercase 3-letter currency code.

    Raises:
        CandidateValidationError: If the currency is invalid.
    """
    currency = normalize_text(value).upper()

    if len(currency) != 3:
        raise CandidateValidationError("Currency must be a 3-letter code.")

    return currency


def normalize_country(value):
    """
    Normalize country code.

    Args:
        value: Raw country.

    Returns:
        str: Uppercase country code.
    """
    return normalize_text(value).upper()


def parse_decimal(value, field_name, required=False):
    """
    Parse a decimal value safely.

    Args:
        value: Raw decimal value.
        field_name: Field name used in error messages.
        required: Whether the value is mandatory.

    Returns:
        Decimal or None.

    Raises:
        CandidateValidationError: If parsing fails.
    """
    if value is None or value == "":
        if required:
            raise CandidateValidationError(f"{field_name} is required.")

        return None

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CandidateValidationError(
            f"{field_name} must be a valid decimal."
        ) from exc


def parse_date(value, field_name, required=False):
    """
    Parse a date value safely.

    Args:
        value: Raw date value in YYYY-MM-DD format.
        field_name: Field name used in error messages.
        required: Whether the value is mandatory.

    Returns:
        date or None.

    Raises:
        CandidateValidationError: If parsing fails.
    """
    if value is None or value == "":
        if required:
            raise CandidateValidationError(f"{field_name} is required.")

        return None

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise CandidateValidationError(
            f"{field_name} must be in YYYY-MM-DD format."
        ) from exc


def parse_datetime(value):
    """
    Parse a datetime value safely.

    Args:
        value: Raw datetime value.

    Returns:
        datetime or None.
    """
    if not value:
        return None

    if isinstance(value, datetime):
        parsed_value = value
    else:
        parsed_value = django_parse_datetime(str(value).strip())

    if parsed_value is None:
        return None

    if timezone.is_naive(parsed_value):
        return timezone.make_aware(parsed_value, timezone.get_current_timezone())

    return parsed_value



def parse_integer(value, default=1):
    """
    Parse an integer value safely.

    Args:
        value: Raw integer-like value.
        default: Fallback integer.

    Returns:
        int: Parsed integer or default.
    """
    if value is None or value == "":
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def remove_backend_calculated_fields_from_missing_fields(
    missing_fields,
    calculated_fields,
):
    """
    Remove fields from missing_fields when backend calculated them.

    Args:
        missing_fields: Original missing fields.
        calculated_fields: Fields calculated by the backend.

    Returns:
        list: Cleaned missing field names.
    """
    calculated_set = {field.lower() for field in calculated_fields}

    return [
        field
        for field in missing_fields
        if str(field).lower() not in calculated_set
    ]


def build_research_payload_with_backend_calculations(
    raw_candidate,
    metric_result,
):
    """
    Attach backend calculation metadata to a candidate payload.

    Args:
        raw_candidate: Original provider candidate dictionary.
        metric_result: Result from calculate_basic_bond_metrics().

    Returns:
        dict: Payload with backend calculation metadata.
    """
    payload = dict(raw_candidate)
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


def build_summary_with_backend_calculations(summary, metric_result):
    """
    Append backend calculation notes to provider/AI summary text.

    Args:
        summary: Existing summary text.
        metric_result: Result from calculate_basic_bond_metrics().

    Returns:
        str: Combined summary text.
    """
    combined_summary = summary.strip()

    if metric_result["calculation_notes"]:
        if combined_summary:
            combined_summary += " "

        combined_summary += metric_result["calculation_notes"]

    return combined_summary



def normalize_string_list(values):
    """
    Normalize a list of string values.

    Args:
        values: Raw list or None.

    Returns:
        list[str]: Uppercase cleaned unique values.
    """
    if not values:
        return []

    normalized_values = []

    for value in values:
        normalized_value = normalize_text(value).upper()

        if normalized_value and normalized_value not in normalized_values:
            normalized_values.append(normalized_value)

    return normalized_values


def normalize_list(values):
    """
    Normalize a generic list.

    Args:
        values: Raw list, tuple, string or None.

    Returns:
        list: Clean list.
    """
    if values is None:
        return []

    if isinstance(values, list):
        return values

    if isinstance(values, tuple):
        return list(values)

    if values == "":
        return []

    return [values]


def normalize_choice(value, choices_class, default_value):
    """
    Normalize a TextChoices-compatible value.

    Args:
        value: Raw value.
        choices_class: Django TextChoices class.
        default_value: Fallback choice value.

    Returns:
        str: Valid choice value.
    """
    if not value:
        return default_value

    raw_value = normalize_text(value)
    allowed_values = list(choices_class.values)

    if raw_value in allowed_values:
        return raw_value

    upper_value = raw_value.upper()

    for allowed_value in allowed_values:
        if upper_value == str(allowed_value).upper():
            return allowed_value

    return default_value


def normalize_boolean(value, default=False):
    """
    Normalize a boolean-like value.

    Args:
        value: Raw boolean-like value.
        default: Fallback value.

    Returns:
        bool: Normalized boolean.
    """
    if value is None or value == "":
        return default

    if isinstance(value, bool):
        return value

    normalized_value = normalize_text(value).lower()

    if normalized_value in ["true", "1", "yes", "y"]:
        return True

    if normalized_value in ["false", "0", "no", "n"]:
        return False

    return default


def normalize_raw_candidate(raw_candidate):
    """
    Normalize and validate one raw candidate dictionary.

    Args:
        raw_candidate: Raw candidate dictionary from a provider.

    Returns:
        dict: Normalized candidate data.

    Raises:
        CandidateValidationError: If required data is missing or invalid.
    """
    isin = normalize_isin(raw_candidate.get("isin"))

    if not isin:
        raise CandidateValidationError("ISIN is required.")

    name = normalize_text(raw_candidate.get("name"))

    if not name:
        raise CandidateValidationError("Name is required.")

    issuer = normalize_text(raw_candidate.get("issuer"))

    if not issuer:
        raise CandidateValidationError("Issuer is required.")

    currency = normalize_currency(raw_candidate.get("currency"))
    country = normalize_country(raw_candidate.get("country"))

    maturity_date = parse_date(
        raw_candidate.get("maturity_date"),
        field_name="maturity_date",
        required=True,
    )

    raw_rating = normalize_text(raw_candidate.get("credit_rating"))

    try:
        credit_rating = normalize_rating(raw_rating)
    except RatingError as exc:
        raise CandidateValidationError(str(exc)) from exc

    coupon_rate = parse_decimal(
        raw_candidate.get("coupon_rate"),
        field_name="coupon_rate",
        required=True,
    )
    market_price = parse_decimal(
        raw_candidate.get("market_price"),
        field_name="market_price",
        required=True,
    )
    ytm = parse_decimal(
        raw_candidate.get("ytm"),
        field_name="ytm",
    )
    duration = parse_decimal(
        raw_candidate.get("duration"),
        field_name="duration",
    )
    coupon_frequency = parse_integer(
        raw_candidate.get("coupon_frequency"),
        default=1,
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
        raise CandidateValidationError(
            "YTM is missing and could not be calculated by the backend."
        )

    if metric_result["duration"] is None:
        raise CandidateValidationError(
            "Duration is missing and could not be calculated by the backend."
        )

    missing_fields = remove_backend_calculated_fields_from_missing_fields(
        missing_fields=normalize_list(raw_candidate.get("missing_fields")),
        calculated_fields=metric_result["calculated_fields"],
    )
    research_payload = build_research_payload_with_backend_calculations(
        raw_candidate=raw_candidate,
        metric_result=metric_result,
    )
    ai_summary = build_summary_with_backend_calculations(
        summary=normalize_text(raw_candidate.get("ai_summary")),
        metric_result=metric_result,
    )

    return {
        "isin": isin,
        "name": name,
        "issuer": issuer,
        "country": country,
        "currency": currency,
        "bond_type": normalize_text(raw_candidate.get("bond_type")).upper(),
        "coupon_rate": coupon_rate,
        "maturity_date": maturity_date,
        "credit_rating": credit_rating,
        "rating_source": normalize_text(raw_candidate.get("rating_source")),
        "market_price": market_price,
        "ytm": metric_result["ytm"],
        "duration": metric_result["duration"],
        "source": normalize_text(raw_candidate.get("source")),
        "source_url": normalize_text(raw_candidate.get("source_url")),
        "data_origin": normalize_choice(
            raw_candidate.get("data_origin"),
            DataOrigin,
            DataOrigin.OTHER,
        ),
        "retrieved_at": parse_datetime(raw_candidate.get("retrieved_at")),
        "confidence": normalize_choice(
            raw_candidate.get("confidence"),
            ResearchConfidence,
            ResearchConfidence.LOW,
        ),
        "needs_review": normalize_boolean(
            raw_candidate.get("needs_review"),
            default=True,
        ),
        "review_status": normalize_choice(
            raw_candidate.get("review_status"),
            ReviewStatus,
            ReviewStatus.NEEDS_REVIEW,
        ),
        "missing_fields": missing_fields,
        "research_payload": research_payload,
        "ai_summary": ai_summary,
        "ai_reasoning": normalize_text(raw_candidate.get("ai_reasoning")),
    }


def candidate_passes_optional_filters(
    candidate,
    currencies,
    countries,
    bond_types=None,
):
    """
    Check optional currency, country and bond type filters.

    Args:
        candidate: Normalized candidate dictionary.
        currencies: Allowed currencies.
        countries: Allowed countries.
        bond_types: Allowed bond types.

    Returns:
        bool: True if the candidate passes filters.
    """
    bond_types = bond_types or []

    if currencies and candidate["currency"] not in currencies:
        return False

    if countries and candidate["country"] not in countries:
        return False

    if bond_types and candidate.get("bond_type") not in bond_types:
        return False

    return True


def candidate_is_active_for_user(user, isin):
    """
    Check whether a candidate ISIN already exists in user's active holdings.

    Args:
        user: Authenticated user.
        isin: Candidate ISIN.

    Returns:
        bool: True if active in Portfolio or Watchlist.
    """
    return UserBond.objects.filter(
        user=user,
        bond__isin=isin,
        is_active=True,
    ).exists()


def should_skip_existing_candidate(existing_candidate):
    """
    Decide whether an existing candidate should be skipped.

    Args:
        existing_candidate: BondCandidate instance or None.

    Returns:
        bool: True if existing status should not be overwritten.
    """
    if existing_candidate is None:
        return False

    return existing_candidate.status in [
        BondCandidate.Status.ADDED_TO_WATCHLIST,
        BondCandidate.Status.IGNORED,
    ]


def save_or_update_candidate(user, discovery_run, candidate):
    """
    Save or update one candidate for the user.

    Args:
        user: Authenticated user.
        discovery_run: DiscoveryRun instance.
        candidate: Normalized candidate dictionary.

    Returns:
        tuple[BondCandidate, bool]: Candidate and created flag.
    """
    existing_candidate = BondCandidate.objects.filter(
        user=user,
        isin=candidate["isin"],
    ).first()

    if should_skip_existing_candidate(existing_candidate):
        return existing_candidate, False

    defaults = {
        "discovery_run": discovery_run,
        "name": candidate["name"],
        "issuer": candidate["issuer"],
        "country": candidate["country"],
        "currency": candidate["currency"],
        "coupon_rate": candidate["coupon_rate"],
        "maturity_date": candidate["maturity_date"],
        "credit_rating": candidate["credit_rating"],
        "rating_source": candidate["rating_source"],
        "market_price": candidate["market_price"],
        "ytm": candidate["ytm"],
        "duration": candidate["duration"],
        "source": candidate["source"],
        "source_url": candidate["source_url"],
        "data_origin": candidate["data_origin"],
        "retrieved_at": candidate["retrieved_at"],
        "confidence": candidate["confidence"],
        "needs_review": candidate["needs_review"],
        "review_status": candidate["review_status"],
        "missing_fields": candidate["missing_fields"],
        "research_payload": candidate["research_payload"],
        "ai_summary": candidate["ai_summary"],
        "ai_reasoning": candidate["ai_reasoning"],
        "status": BondCandidate.Status.NEW,
    }

    candidate_object, created = BondCandidate.objects.update_or_create(
        user=user,
        isin=candidate["isin"],
        defaults=defaults,
    )

    return candidate_object, created


@transaction.atomic
def run_bond_discovery(
    user,
    source=DEFAULT_DISCOVERY_SOURCE,
    min_rating=INVESTMENT_GRADE_MIN_RATING,
    currencies=None,
    countries=None,
    bond_types=None,
):
    """
    Run bond discovery for a user.

    Args:
        user: Authenticated user.
        source: Provider source name.
        min_rating: Minimum accepted rating.
        currencies: Optional list of allowed currencies.
        countries: Optional list of allowed countries.
        bond_types: Optional list of allowed bond types.

    Returns:
        DiscoveryRun: Completed discovery run.

    Raises:
        DiscoveryServiceError: If discovery cannot run.
    """
    try:
        provider = get_provider(source)
    except ProviderRegistryError as exc:
        raise DiscoveryServiceError(str(exc)) from exc

    try:
        normalized_min_rating = normalize_rating(min_rating)
    except RatingError as exc:
        raise DiscoveryServiceError(str(exc)) from exc

    normalized_currencies = normalize_string_list(currencies)
    normalized_countries = normalize_string_list(countries)
    normalized_bond_types = normalize_string_list(bond_types)

    discovery_run = DiscoveryRun.objects.create(
        user=user,
        source=provider.get_provider_name(),
        min_rating=normalized_min_rating,
        currencies=normalized_currencies,
        countries=normalized_countries,
    )
    discovery_run.mark_running()

    total_found = 0
    total_saved = 0
    total_skipped = 0
    seen_isins = set()

    try:
        raw_candidates = provider.load_candidates()
        total_found = len(raw_candidates)

        for raw_candidate in raw_candidates:
            try:
                candidate = normalize_raw_candidate(raw_candidate)
            except CandidateValidationError:
                total_skipped += 1
                continue

            if candidate["isin"] in seen_isins:
                total_skipped += 1
                continue

            seen_isins.add(candidate["isin"])

            if not candidate_passes_optional_filters(
                candidate=candidate,
                currencies=normalized_currencies,
                countries=normalized_countries,
                bond_types=normalized_bond_types,
            ):
                total_skipped += 1
                continue

            if candidate["maturity_date"] <= timezone.localdate():
                total_skipped += 1
                continue

            if not is_rating_at_least(
                candidate["credit_rating"],
                minimum_rating=normalized_min_rating,
            ):
                total_skipped += 1
                continue

            if candidate_is_active_for_user(
                user=user,
                isin=candidate["isin"],
            ):
                total_skipped += 1
                continue

            existing_candidate = BondCandidate.objects.filter(
                user=user,
                isin=candidate["isin"],
            ).first()

            if should_skip_existing_candidate(existing_candidate):
                total_skipped += 1
                continue

            save_or_update_candidate(
                user=user,
                discovery_run=discovery_run,
                candidate=candidate,
            )
            total_saved += 1

        discovery_run.mark_completed(
            total_found=total_found,
            total_saved=total_saved,
            total_skipped=total_skipped,
        )

        return discovery_run

    except Exception as exc:
        discovery_run.mark_failed(str(exc))

        raise DiscoveryServiceError(str(exc)) from exc


def get_visible_candidates(user):
    """
    Return visible candidates for the authenticated user.

    Visible means:
    - belongs to the user
    - status is NEW or REVIEWED
    - not already active in Portfolio or Watchlist

    Args:
        user: Authenticated user.

    Returns:
        QuerySet[BondCandidate]
    """
    active_user_isins = UserBond.objects.filter(
        user=user,
        is_active=True,
    ).values_list("bond__isin", flat=True)

    return (
        BondCandidate.objects.filter(
            user=user,
            status__in=[
                BondCandidate.Status.NEW,
                BondCandidate.Status.REVIEWED,
            ],
        )
        .exclude(isin__in=active_user_isins)
        .order_by("maturity_date", "isin")
    )


def get_candidate_for_user(user, candidate_id):
    """
    Get one candidate owned by the authenticated user.

    Args:
        user: Authenticated user.
        candidate_id: BondCandidate id.

    Returns:
        BondCandidate instance.

    Raises:
        BondCandidate.DoesNotExist: If not found.
    """
    return BondCandidate.objects.get(
        id=candidate_id,
        user=user,
    )


def create_bond_from_candidate(candidate):
    """
    Create or get Bond master data from a candidate.

    Args:
        candidate: BondCandidate instance.

    Returns:
        Bond instance.
    """
    bond, _created = Bond.objects.get_or_create(
        isin=candidate.isin,
        defaults={
            "name": candidate.name,
            "issuer": candidate.issuer,
            "bond_type": Bond.BondType.OTHER,
            "currency": candidate.currency,
            "seniority": Bond.Seniority.OTHER,
            "is_callable": False,
            "market_liquidity": Bond.MarketLiquidity.MEDIUM,
            "credit_rating": candidate.credit_rating,
            "face_value": Decimal("100.00"),
            "annual_coupon_rate": candidate.coupon_rate,
            "coupon_frequency": 1,
            "maturity_date": candidate.maturity_date,
        },
    )

    return bond


def build_market_data_notes_from_candidate(candidate):
    """
    Build market data notes from candidate research information.

    Args:
        candidate: BondCandidate instance.

    Returns:
        str: Notes for BondMarketData.
    """
    if candidate.ai_summary:
        return candidate.ai_summary

    if candidate.ai_reasoning:
        return candidate.ai_reasoning

    return "Created from discovery candidate."


def create_or_update_market_data_from_candidate(candidate, bond):
    """
    Create or update market data from candidate data.

    This function intentionally propagates discovery/AI research metadata
    from BondCandidate to BondMarketData so the Watchlist keeps traceability.

    Args:
        candidate: BondCandidate instance.
        bond: Bond instance.

    Returns:
        BondMarketData instance or None.
    """
    if candidate.market_price is None:
        return None

    source = candidate.source or "discovery_candidate"
    quote_date = timezone.localdate()

    market_data, _created = BondMarketData.objects.update_or_create(
        bond=bond,
        quote_date=quote_date,
        source=source,
        defaults={
            "market_price": candidate.market_price,
            "ytm": candidate.ytm,
            "source_url": candidate.source_url,
            "data_origin": candidate.data_origin,
            "retrieved_at": candidate.retrieved_at,
            "confidence": candidate.confidence,
            "needs_review": candidate.needs_review,
            "review_status": candidate.review_status,
            "missing_fields": candidate.missing_fields or [],
            "research_payload": candidate.research_payload or {},
            "is_manual": False,
            "notes": build_market_data_notes_from_candidate(candidate),
        },
    )

    return market_data


@transaction.atomic
def add_candidate_to_watchlist(user, candidate_id):
    """
    Add a discovered candidate to the user's Watchlist.

    Args:
        user: Authenticated user.
        candidate_id: BondCandidate id.

    Returns:
        UserBond instance.

    Raises:
        DiscoveryServiceError: If the candidate cannot be added.
    """
    candidate = get_candidate_for_user(
        user=user,
        candidate_id=candidate_id,
    )

    if candidate.status == BondCandidate.Status.IGNORED:
        raise DiscoveryServiceError("Ignored candidates cannot be added.")

    bond = create_bond_from_candidate(candidate)

    existing_portfolio_item = UserBond.objects.filter(
        user=user,
        bond=bond,
        holding_type=UserBond.HoldingType.PORTFOLIO,
        is_active=True,
    ).first()

    if existing_portfolio_item is not None:
        raise DiscoveryServiceError(
            "This bond already exists in your Portfolio."
        )

    create_or_update_market_data_from_candidate(
        candidate=candidate,
        bond=bond,
    )

    watchlist_item, created = UserBond.objects.get_or_create(
        user=user,
        bond=bond,
        holding_type=UserBond.HoldingType.WATCHLIST,
        defaults={
            "quantity": Decimal("0.00"),
            "purchase_price": None,
            "base_currency": bond.currency,
            "is_active": True,
        },
    )

    if not created and not watchlist_item.is_active:
        watchlist_item.is_active = True
        watchlist_item.save(
            update_fields=[
                "is_active",
                "updated_at",
            ],
        )

    candidate.status = BondCandidate.Status.ADDED_TO_WATCHLIST
    candidate.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    return watchlist_item


@transaction.atomic
def ignore_candidate(user, candidate_id):
    """
    Ignore a discovered candidate.

    Args:
        user: Authenticated user.
        candidate_id: BondCandidate id.

    Returns:
        BondCandidate instance.
    """
    candidate = get_candidate_for_user(
        user=user,
        candidate_id=candidate_id,
    )
    candidate.status = BondCandidate.Status.IGNORED
    candidate.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    return candidate


