"""
Bond discovery service.

This module contains the backend business logic for the Watchlist Discovery
Engine.

The discovery engine is data-driven:

    Provider data
    -> normalization
    -> validation
    -> rating and maturity filters
    -> user Watchlist/Portfolio exclusion
    -> BondCandidate records

Important:
    This service does not use AI as a data source.
    It only consumes provider data and applies deterministic backend rules.

The MVP uses a static provider. Later, this service can consume a CSV provider
or an external API provider without changing the frontend flow.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from bonds.discovery.providers import static_provider
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
    DiscoveryRun,
)
from portfolios.models import UserBond


DEFAULT_DISCOVERY_SOURCE = "static_provider"


class DiscoveryServiceError(Exception):
    """
    Raised when the discovery service cannot complete a requested action.
    """


class CandidateValidationError(ValueError):
    """
    Raised when a raw provider candidate is missing required or valid data.
    """


def normalize_text(value):
    """
    Normalize text values.

    Args:
        value: Any raw value.

    Returns:
        Stripped string.
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
        Uppercase ISIN without spaces.

    Raises:
        CandidateValidationError: If ISIN is missing.
    """
    normalized_value = normalize_text(value).upper().replace(" ", "")

    if not normalized_value:
        raise CandidateValidationError("ISIN is required.")

    return normalized_value


def normalize_currency(value):
    """
    Normalize currency code.

    Args:
        value: Raw currency value.

    Returns:
        Uppercase 3-letter currency code.

    Raises:
        CandidateValidationError: If currency is missing or invalid.
    """
    normalized_value = normalize_text(value).upper()

    if not normalized_value:
        raise CandidateValidationError("Currency is required.")

    if len(normalized_value) != 3:
        raise CandidateValidationError(
            f"Invalid currency code: {normalized_value}"
        )

    return normalized_value


def normalize_country(value):
    """
    Normalize country code.

    Args:
        value: Raw country value.

    Returns:
        Uppercase country code or empty string.
    """
    normalized_value = normalize_text(value).upper()

    if not normalized_value:
        return ""

    return normalized_value


def parse_decimal(value, field_name, required=False):
    """
    Parse a Decimal value from provider data.

    Args:
        value: Raw numeric value.
        field_name: Field name used in error messages.
        required: Whether the value is required.

    Returns:
        Decimal value or None.

    Raises:
        CandidateValidationError: If required or invalid.
    """
    if value is None or value == "":
        if required:
            raise CandidateValidationError(f"{field_name} is required.")

        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CandidateValidationError(
            f"{field_name} must be a valid decimal number."
        ) from exc


def parse_date(value, field_name, required=False):
    """
    Parse a date value from provider data.

    Args:
        value: Raw date value.
        field_name: Field name used in error messages.
        required: Whether the value is required.

    Returns:
        date object or None.

    Raises:
        CandidateValidationError: If required or invalid.
    """
    if value is None or value == "":
        if required:
            raise CandidateValidationError(f"{field_name} is required.")

        return None

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise CandidateValidationError(
            f"{field_name} must use YYYY-MM-DD format."
        ) from exc


def normalize_string_list(values, max_length=None):
    """
    Normalize optional string filter lists.

    Args:
        values: Iterable of string-like values or None.
        max_length: Optional exact string length filter.

    Returns:
        List of uppercase stripped strings.
    """
    if not values:
        return []

    normalized_values = []

    for value in values:
        normalized_value = normalize_text(value).upper()

        if not normalized_value:
            continue

        if max_length is not None and len(normalized_value) != max_length:
            continue

        normalized_values.append(normalized_value)

    return normalized_values


def get_provider(source):
    """
    Return a discovery provider module by source name.

    Args:
        source: Provider name.

    Returns:
        Provider module.

    Raises:
        DiscoveryServiceError: If provider is unsupported.
    """
    normalized_source = normalize_text(source) or DEFAULT_DISCOVERY_SOURCE

    if normalized_source == static_provider.get_provider_name():
        return static_provider

    raise DiscoveryServiceError(
        f"Unsupported discovery source: {normalized_source}"
    )


def normalize_raw_candidate(raw_candidate):
    """
    Normalize and validate one raw provider candidate.

    Args:
        raw_candidate: Raw provider dictionary.

    Returns:
        Normalized candidate dictionary.

    Raises:
        CandidateValidationError: If required data is missing or invalid.
    """
    if not isinstance(raw_candidate, dict):
        raise CandidateValidationError(
            "Provider candidate must be a dictionary."
        )

    isin = normalize_isin(raw_candidate.get("isin"))
    name = normalize_text(raw_candidate.get("name"))
    issuer = normalize_text(raw_candidate.get("issuer"))
    currency = normalize_currency(raw_candidate.get("currency"))
    maturity_date = parse_date(
        raw_candidate.get("maturity_date"),
        field_name="maturity_date",
        required=True,
    )
    credit_rating = normalize_rating(raw_candidate.get("credit_rating"))

    if not name:
        raise CandidateValidationError("Bond name is required.")

    if not issuer:
        raise CandidateValidationError("Issuer is required.")

    return {
        "isin": isin,
        "name": name,
        "issuer": issuer,
        "country": normalize_country(raw_candidate.get("country")),
        "currency": currency,
        "coupon_rate": parse_decimal(
            raw_candidate.get("coupon_rate"),
            field_name="coupon_rate",
            required=False,
        ),
        "maturity_date": maturity_date,
        "credit_rating": credit_rating,
        "rating_source": normalize_text(raw_candidate.get("rating_source")),
        "market_price": parse_decimal(
            raw_candidate.get("market_price"),
            field_name="market_price",
            required=False,
        ),
        "ytm": parse_decimal(
            raw_candidate.get("ytm"),
            field_name="ytm",
            required=False,
        ),
        "duration": parse_decimal(
            raw_candidate.get("duration"),
            field_name="duration",
            required=False,
        ),
        "source": normalize_text(raw_candidate.get("source"))
        or DEFAULT_DISCOVERY_SOURCE,
        "source_url": normalize_text(raw_candidate.get("source_url")),
    }


def candidate_passes_optional_filters(candidate, currencies, countries):
    """
    Check optional currency and country filters.

    Args:
        candidate: Normalized candidate dictionary.
        currencies: Normalized currency filter list.
        countries: Normalized country filter list.

    Returns:
        True if the candidate passes optional filters.
    """
    if currencies and candidate["currency"] not in currencies:
        return False

    if countries and candidate["country"] not in countries:
        return False

    return True


def candidate_is_active(user, isin):
    """
    Check whether the user already has this ISIN in active Portfolio or Watchlist.

    Args:
        user: Django user.
        isin: Normalized ISIN.

    Returns:
        True if an active UserBond exists for the user's ISIN.
    """
    return UserBond.objects.filter(
        user=user,
        is_active=True,
        bond__isin=isin,
    ).exists()


def should_skip_existing_candidate(existing_candidate):
    """
    Decide whether an existing candidate should be skipped.

    Args:
        existing_candidate: Existing BondCandidate or None.

    Returns:
        True when the candidate should not be updated or shown again.
    """
    if existing_candidate is None:
        return False

    return existing_candidate.status in {
        BondCandidate.Status.ADDED_TO_WATCHLIST,
        BondCandidate.Status.IGNORED,
    }


def save_or_update_candidate(user, discovery_run, candidate):
    """
    Save or update a BondCandidate for a user and ISIN.

    Existing NEW or REVIEWED candidates are updated with fresh provider data.
    Existing IGNORED or ADDED_TO_WATCHLIST candidates are skipped before this
    function is called.

    Args:
        user: Django user.
        discovery_run: DiscoveryRun instance.
        candidate: Normalized candidate dictionary.

    Returns:
        BondCandidate instance.
    """
    existing_candidate = BondCandidate.objects.filter(
        user=user,
        isin=candidate["isin"],
    ).first()

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
    }

    if existing_candidate is not None:
        for field_name, value in defaults.items():
            setattr(existing_candidate, field_name, value)

        existing_candidate.save()
        return existing_candidate

    return BondCandidate.objects.create(
        user=user,
        isin=candidate["isin"],
        status=BondCandidate.Status.NEW,
        **defaults,
    )


@transaction.atomic
def run_bond_discovery(
    user,
    source=DEFAULT_DISCOVERY_SOURCE,
    min_rating=INVESTMENT_GRADE_MIN_RATING,
    currencies=None,
    countries=None,
):
    """
    Run the bond discovery flow for one user.

    Args:
        user: Authenticated Django user.
        source: Provider name.
        min_rating: Minimum accepted rating. Default: BBB-.
        currencies: Optional list of accepted currencies.
        countries: Optional list of accepted country codes.

    Returns:
        DiscoveryRun instance.

    Notes:
        Skipped candidates are not stored as separate error rows in the MVP.
        Run totals show how many candidates were skipped.
    """
    provider = get_provider(source)
    normalized_source = provider.get_provider_name()
    normalized_min_rating = normalize_rating(min_rating)
    normalized_currencies = normalize_string_list(
        values=currencies,
        max_length=3,
    )
    normalized_countries = normalize_string_list(
        values=countries,
        max_length=2,
    )

    discovery_run = DiscoveryRun.objects.create(
        user=user,
        source=normalized_source,
        min_rating=normalized_min_rating,
        currencies=normalized_currencies,
        countries=normalized_countries,
        status=DiscoveryRun.Status.RUNNING,
        started_at=timezone.now(),
    )

    total_found = 0
    total_saved = 0
    total_skipped = 0
    seen_isins = set()
    today = timezone.localdate()

    try:
        raw_candidates = provider.load_candidates()
        total_found = len(raw_candidates)

        for raw_candidate in raw_candidates:
            try:
                candidate = normalize_raw_candidate(raw_candidate)
            except (CandidateValidationError, RatingError):
                total_skipped += 1
                continue

            isin = candidate["isin"]

            if isin in seen_isins:
                total_skipped += 1
                continue

            seen_isins.add(isin)

            if not candidate_passes_optional_filters(
                candidate=candidate,
                currencies=normalized_currencies,
                countries=normalized_countries,
            ):
                total_skipped += 1
                continue

            if candidate["maturity_date"] <= today:
                total_skipped += 1
                continue

            try:
                if not is_rating_at_least(
                    rating=candidate["credit_rating"],
                    minimum_rating=normalized_min_rating,
                ):
                    total_skipped += 1
                    continue
            except RatingError:
                total_skipped += 1
                continue

            if candidate_is_active(
                user=user,
                isin=isin,
            ):
                total_skipped += 1
                continue

            existing_candidate = BondCandidate.objects.filter(
                user=user,
                isin=isin,
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
        raise


def get_visible_candidates(user):
    """
    Return discoverable candidates for a user.

    This function excludes:
    - candidates already added to Watchlist
    - ignored candidates
    - candidates whose ISIN is already active in Portfolio or Watchlist

    Args:
        user: Authenticated Django user.

    Returns:
        QuerySet of visible BondCandidate records.
    """
    active_user_isins = UserBond.objects.filter(
        user=user,
        is_active=True,
    ).values_list(
        "bond__isin",
        flat=True,
    )

    return BondCandidate.objects.filter(
        user=user,
        status__in=[
            BondCandidate.Status.NEW,
            BondCandidate.Status.REVIEWED,
        ],
    ).exclude(
        isin__in=active_user_isins,
    ).order_by(
        "maturity_date",
        "isin",
    )


def get_candidate_for_user(user, candidate_id):
    """
    Return a candidate owned by the user.

    Args:
        user: Authenticated Django user.
        candidate_id: BondCandidate primary key.

    Returns:
        BondCandidate instance.

    Raises:
        BondCandidate.DoesNotExist: If candidate does not exist for user.
    """
    return BondCandidate.objects.get(
        user=user,
        pk=candidate_id,
    )


def create_bond_from_candidate(candidate):
    """
    Create or return a Bond master record from a candidate.

    Existing Bond records are not overwritten. This avoids replacing master
    data with lower-quality discovery provider data.

    Args:
        candidate: BondCandidate instance.

    Returns:
        Bond instance.
    """
    bond, _ = Bond.objects.get_or_create(
        isin=candidate.isin,
        defaults={
            "name": candidate.name,
            "issuer": candidate.issuer,
            "bond_type": Bond.BondType.OTHER,
            "currency": candidate.currency,
            "seniority": Bond.Seniority.OTHER,
            "market_liquidity": Bond.MarketLiquidity.MEDIUM,
            "credit_rating": candidate.credit_rating,
            "annual_coupon_rate": candidate.coupon_rate or Decimal("0.0000"),
            "coupon_frequency": 1,
            "maturity_date": candidate.maturity_date,
        },
    )

    return bond


def create_or_update_market_data_from_candidate(candidate, bond):
    """
    Create or update BondMarketData from candidate data.

    Market data is created only when the candidate has a market price because
    BondMarketData.market_price is required by the model.

    Args:
        candidate: BondCandidate instance.
        bond: Bond instance.

    Returns:
        BondMarketData instance or None.
    """
    if candidate.market_price is None:
        return None

    market_data, _ = BondMarketData.objects.update_or_create(
        bond=bond,
        quote_date=timezone.localdate(),
        source=candidate.source,
        defaults={
            "market_price": candidate.market_price,
            "market_required_return": None,
            "ytm": candidate.ytm,
            "is_manual": False,
            "notes": (
                "Created from a bond discovery candidate. "
                "Provider data should be reviewed before relying on it."
            ),
        },
    )

    return market_data


@transaction.atomic
def add_candidate_to_watchlist(user, candidate_id):
    """
    Add a discovered candidate to the user's Watchlist.

    Flow:
        1. Get the candidate for the current user.
        2. Create the Bond master record if it does not exist.
        3. Create/update market data if the candidate has market price data.
        4. Create or reactivate a WATCHLIST UserBond.
        5. Mark the candidate as ADDED_TO_WATCHLIST.

    Args:
        user: Authenticated Django user.
        candidate_id: BondCandidate primary key.

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
        raise DiscoveryServiceError(
            "Ignored candidates cannot be added to Watchlist."
        )

    bond = create_bond_from_candidate(candidate)

    active_portfolio_item = UserBond.objects.filter(
        user=user,
        bond=bond,
        holding_type=UserBond.HoldingType.PORTFOLIO,
        is_active=True,
    ).first()

    if active_portfolio_item is not None:
        raise DiscoveryServiceError(
            "This bond already exists in your Portfolio."
        )

    create_or_update_market_data_from_candidate(
        candidate=candidate,
        bond=bond,
    )

    existing_watchlist_item = UserBond.objects.filter(
        user=user,
        bond=bond,
        holding_type=UserBond.HoldingType.WATCHLIST,
    ).first()

    if existing_watchlist_item is not None:
        existing_watchlist_item.is_active = True
        existing_watchlist_item.quantity = 0
        existing_watchlist_item.purchase_price = None
        existing_watchlist_item.save(
            update_fields=[
                "is_active",
                "quantity",
                "purchase_price",
                "updated_at",
            ]
        )
        user_bond = existing_watchlist_item
    else:
        user_bond = UserBond.objects.create(
            user=user,
            bond=bond,
            holding_type=UserBond.HoldingType.WATCHLIST,
            quantity=0,
            purchase_price=None,
        )

    candidate.status = BondCandidate.Status.ADDED_TO_WATCHLIST
    candidate.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return user_bond


@transaction.atomic
def ignore_candidate(user, candidate_id):
    """
    Mark a candidate as ignored.

    Args:
        user: Authenticated Django user.
        candidate_id: BondCandidate primary key.

    Returns:
        Updated BondCandidate instance.
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
        ]
    )

    return candidate