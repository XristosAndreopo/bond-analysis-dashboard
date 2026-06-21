"""
External provider test utilities for the Bond Discovery Engine.

This module tests the external JSON/API provider without writing anything to
the database.

It checks:
- whether external API configuration exists
- whether data can be loaded
- whether the response can be mapped
- whether candidates can pass basic normalization
- sample valid candidates

No BondCandidate, Bond, Portfolio or Watchlist records are created here.
"""

from bonds.discovery.discovery_service import (
    CandidateValidationError,
    normalize_raw_candidate,
)
from bonds.discovery.providers import external_json_provider
from bonds.discovery.providers.external_api_client import (
    external_api_is_configured,
    get_auth_header_name,
    get_external_api_key,
    get_external_api_timeout,
    get_external_api_url,
)
from bonds.discovery.providers.provider_health import extract_host_from_url


MAX_ERROR_ITEMS = 10
MAX_SAMPLE_ITEMS = 5


def run_external_provider_test():
    """
    Test the external JSON/API provider safely.

    Returns:
        dict: Test result report.
    """
    api_url = get_external_api_url()
    api_configured = external_api_is_configured()

    result = {
        "source": external_json_provider.get_provider_name(),
        "api_configured": api_configured,
        "api_host": extract_host_from_url(api_url),
        "api_key_configured": bool(get_external_api_key()),
        "api_timeout_seconds": get_external_api_timeout(),
        "api_auth_header": get_auth_header_name(),
        "mode": "external_api" if api_configured else "local_json_fallback",
        "data_loaded": False,
        "loaded_count": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "errors": [],
        "sample_candidates": [],
    }

    try:
        raw_candidates = external_json_provider.load_candidates()
    except Exception as exc:
        result["errors"].append(str(exc))

        return result

    result["data_loaded"] = True
    result["loaded_count"] = len(raw_candidates)

    for index, raw_candidate in enumerate(raw_candidates, start=1):
        try:
            candidate = normalize_raw_candidate(raw_candidate)
        except CandidateValidationError as exc:
            result["invalid_count"] += 1
            append_error(
                result=result,
                message=f"Candidate {index}: {exc}",
            )
            continue

        result["valid_count"] += 1
        append_sample_candidate(
            result=result,
            candidate=candidate,
        )

    return result


def append_error(result, message):
    """
    Append an error if the result has not reached the visible error limit.

    Args:
        result: Test result dictionary.
        message: Error message.
    """
    if len(result["errors"]) < MAX_ERROR_ITEMS:
        result["errors"].append(message)


def append_sample_candidate(result, candidate):
    """
    Append sample candidate data if the sample limit has not been reached.

    Args:
        result: Test result dictionary.
        candidate: Normalized candidate dictionary.
    """
    if len(result["sample_candidates"]) >= MAX_SAMPLE_ITEMS:
        return

    result["sample_candidates"].append(
        {
            "isin": candidate["isin"],
            "name": candidate["name"],
            "issuer": candidate["issuer"],
            "country": candidate["country"],
            "currency": candidate["currency"],
            "credit_rating": candidate["credit_rating"],
            "maturity_date": candidate["maturity_date"].isoformat(),
            "market_price": (
                str(candidate["market_price"])
                if candidate["market_price"] is not None
                else ""
            ),
            "ytm": (
                str(candidate["ytm"])
                if candidate["ytm"] is not None
                else ""
            ),
            "duration": (
                str(candidate["duration"])
                if candidate["duration"] is not None
                else ""
            ),
        }
    )