"""
FX rate update services.

This module fetches latest FX rates from the Frankfurter public API and stores
them in the FXRate model.

Important:
    This implementation uses only Python standard library modules. It does not
    require the external 'requests' package.

Frankfurter v2 endpoint used:
    https://api.frankfurter.dev/v2/rate/{base_currency}/{quote_currency}

Design decision:
    The FXRate model stores rates in this format:

        1 base_currency = rate quote_currency

    Example:
        base_currency = USD
        quote_currency = EUR
        rate = 0.92000000

    Meaning:
        1 USD = 0.92 EUR
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db import transaction
from django.utils import timezone

from bonds.models import FXRate


FRANKFURTER_RATE_URL = "https://api.frankfurter.dev/v2/rate"
DEFAULT_TIMEOUT_SECONDS = 15


class FXRateUpdateError(Exception):
    """
    Raised when live FX rates cannot be fetched or parsed.
    """


@dataclass
class FXRateUpdateResult:
    """
    Result object returned after updating one FX rate.

    Attributes:
        base_currency: Currency being converted from.
        quote_currency: Currency being converted to.
        rate_date: Rate date returned by the provider.
        rate: Decimal conversion rate.
        created: True if a new DB row was created, False if updated.
    """

    base_currency: str
    quote_currency: str
    rate_date: object
    rate: Decimal
    created: bool


def normalize_currency(currency):
    """
    Normalize a currency code.

    Args:
        currency: Currency code.

    Returns:
        Uppercase 3-letter currency code.

    Raises:
        FXRateUpdateError: If currency is empty or invalid.
    """
    if not currency:
        raise FXRateUpdateError("Currency code is required.")

    normalized_currency = str(currency).upper().strip()

    if len(normalized_currency) != 3:
        raise FXRateUpdateError(
            f"Invalid currency code: {normalized_currency}"
        )

    return normalized_currency


def decimal_from_api_value(value):
    """
    Convert an API numeric value to Decimal.

    Args:
        value: API numeric value.

    Returns:
        Decimal value.

    Raises:
        FXRateUpdateError: If value cannot be converted.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FXRateUpdateError(
            f"Invalid FX rate value received from API: {value}"
        ) from exc


def fetch_json_from_url(url):
    """
    Fetch JSON data from a URL using Python standard library.

    Args:
        url: Full URL.

    Returns:
        Parsed JSON payload as dictionary.

    Raises:
        FXRateUpdateError: If the HTTP request or JSON parsing fails.
    """
    request = Request(
        url=url,
        headers={
            "User-Agent": (
                "bond-analysis-dashboard/1.0 "
                "(local-development; contact: github.com/XristosAndreopo)"
            ),
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as exc:
        raise FXRateUpdateError(
            f"FX API returned HTTP error {exc.code}: {exc.reason}"
        ) from exc
    except URLError as exc:
        raise FXRateUpdateError(
            f"Could not connect to FX API: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise FXRateUpdateError(
            "FX API request timed out."
        ) from exc

    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise FXRateUpdateError(
            "FX API returned invalid JSON."
        ) from exc


def fetch_latest_rate(base_currency, quote_currency):
    """
    Fetch latest FX rate from Frankfurter v2 single-rate endpoint.

    Args:
        base_currency: Currency being converted from.
        quote_currency: Currency being converted to.

    Returns:
        Dictionary with:
            date: provider rate date
            rate: Decimal rate

    Raises:
        FXRateUpdateError: If request or parsing fails.
    """
    base_currency = normalize_currency(base_currency)
    quote_currency = normalize_currency(quote_currency)

    if base_currency == quote_currency:
        return {
            "date": timezone.localdate(),
            "rate": Decimal("1.00000000"),
        }

    url = f"{FRANKFURTER_RATE_URL}/{base_currency}/{quote_currency}"
    payload = fetch_json_from_url(url)

    provider_date = payload.get("date")
    rate_value = payload.get("rate")

    if not provider_date:
        raise FXRateUpdateError(
            f"Frankfurter response did not include a date for "
            f"{base_currency}/{quote_currency}."
        )

    if rate_value is None:
        raise FXRateUpdateError(
            f"Frankfurter response did not include rate for "
            f"{base_currency}/{quote_currency}."
        )

    return {
        "date": provider_date,
        "rate": decimal_from_api_value(rate_value),
    }


@transaction.atomic
def update_latest_fx_rate(base_currency, quote_currency, source="frankfurter"):
    """
    Fetch and save the latest FX rate for one currency pair.

    Args:
        base_currency: Currency being converted from.
        quote_currency: Currency being converted to.
        source: Provider/source label.

    Returns:
        FXRateUpdateResult instance.
    """
    base_currency = normalize_currency(base_currency)
    quote_currency = normalize_currency(quote_currency)

    api_result = fetch_latest_rate(
        base_currency=base_currency,
        quote_currency=quote_currency,
    )

    fx_rate, created = FXRate.objects.update_or_create(
        base_currency=base_currency,
        quote_currency=quote_currency,
        rate_date=api_result["date"],
        source=source,
        defaults={
            "rate": api_result["rate"],
            "notes": "Automatically fetched from Frankfurter public API v2.",
        },
    )

    return FXRateUpdateResult(
        base_currency=fx_rate.base_currency,
        quote_currency=fx_rate.quote_currency,
        rate_date=fx_rate.rate_date,
        rate=fx_rate.rate,
        created=created,
    )


def update_latest_fx_rates(
    quote_currency="EUR",
    base_currencies=None,
    source="frankfurter",
):
    """
    Fetch and save latest FX rates for multiple currencies.

    Args:
        quote_currency: Target portfolio currency, usually EUR.
        base_currencies: List of currencies to convert from.
        source: Provider/source label.

    Returns:
        Dict with:
            updated: list of FXRateUpdateResult
            errors: list of error strings
    """
    quote_currency = normalize_currency(quote_currency)

    if base_currencies is None:
        base_currencies = [
            "USD",
            "GBP",
            "CHF",
            "JPY",
            "CAD",
            "AUD",
        ]

    updated_results = []
    errors = []

    for base_currency in base_currencies:
        base_currency = normalize_currency(base_currency)

        if base_currency == quote_currency:
            continue

        try:
            result = update_latest_fx_rate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                source=source,
            )
            updated_results.append(result)
        except FXRateUpdateError as exc:
            errors.append(str(exc))

    return {
        "updated": updated_results,
        "errors": errors,
    }