"""
External JSON provider for the Bond Discovery Engine.

This provider can load discovered bond candidates from:

1. A configured external JSON API, if:
       BOND_DISCOVERY_EXTERNAL_API_URL is set

2. A local fallback JSON file, if no API URL is configured:
       backend/bonds/discovery/data/external_bond_universe.json

Purpose:
    This is a safe bridge toward future real API integration.

Important:
    This provider only loads raw dictionaries.

Validation, rating filtering, maturity filtering, duplicate checks and
Watchlist/Portfolio exclusion remain inside discovery_service.py.
"""

import json
from pathlib import Path

from bonds.discovery.providers.external_api_client import (
    ExternalAPIClientError,
    external_api_is_configured,
    fetch_external_json_data,
)


SOURCE_NAME = "external_json_provider"

JSON_FILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "external_bond_universe.json"
)

REQUIRED_FIELDS = [
    "isin",
    "name",
    "issuer",
    "country",
    "currency",
    "coupon_rate",
    "maturity_date",
    "credit_rating",
    "rating_source",
    "market_price",
    "ytm",
    "duration",
    "source",
    "source_url",
]


class ExternalJSONProviderError(Exception):
    """
    Raised when the external JSON provider cannot load candidate data.
    """


def get_provider_name():
    """
    Return the provider identifier.

    Returns:
        str: Provider name.
    """
    return SOURCE_NAME


def load_candidates():
    """
    Load raw bond candidates from external API or local JSON fallback.

    Returns:
        list[dict]: Raw candidate dictionaries.

    Raises:
        ExternalJSONProviderError: If data cannot be loaded or validated.
    """
    if external_api_is_configured():
        raw_data = load_candidates_from_external_api()
    else:
        raw_data = load_candidates_from_local_json()

    return normalize_candidate_collection(raw_data)


def load_candidates_from_external_api():
    """
    Load raw JSON data from the configured external API.

    Returns:
        object: Parsed JSON response.

    Raises:
        ExternalJSONProviderError: If the API request fails.
    """
    try:
        return fetch_external_json_data()
    except ExternalAPIClientError as exc:
        raise ExternalJSONProviderError(str(exc)) from exc


def load_candidates_from_local_json():
    """
    Load raw JSON data from local fallback file.

    Returns:
        object: Parsed JSON file content.

    Raises:
        ExternalJSONProviderError: If the local file is missing or invalid.
    """
    if not JSON_FILE_PATH.exists():
        raise ExternalJSONProviderError(
            f"External JSON discovery file was not found: {JSON_FILE_PATH}"
        )

    try:
        return json.loads(JSON_FILE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExternalJSONProviderError(
            "External JSON discovery file contains invalid JSON."
        ) from exc


def normalize_candidate_collection(raw_data):
    """
    Normalize the JSON response into a list of candidate dictionaries.

    Supported response formats:
        1. Direct list:
            [
                {"isin": "..."}
            ]

        2. Wrapped response:
            {
                "results": [
                    {"isin": "..."}
                ]
            }

        3. Wrapped response:
            {
                "candidates": [
                    {"isin": "..."}
                ]
            }

    Args:
        raw_data: Parsed JSON data.

    Returns:
        list[dict]: Normalized candidate dictionaries.

    Raises:
        ExternalJSONProviderError: If the response format is unsupported.
    """
    if isinstance(raw_data, list):
        candidate_items = raw_data
    elif isinstance(raw_data, dict):
        candidate_items = extract_candidates_from_dict(raw_data)
    else:
        raise ExternalJSONProviderError(
            "External JSON data must be a list or an object containing candidates."
        )

    candidates = []

    for index, item in enumerate(candidate_items, start=1):
        candidates.append(
            normalize_json_item(
                item=item,
                index=index,
            )
        )

    return candidates


def extract_candidates_from_dict(raw_data):
    """
    Extract candidate list from a wrapped JSON response.

    Args:
        raw_data: Parsed JSON object.

    Returns:
        list: Candidate items.

    Raises:
        ExternalJSONProviderError: If no supported list field exists.
    """
    if isinstance(raw_data.get("results"), list):
        return raw_data["results"]

    if isinstance(raw_data.get("candidates"), list):
        return raw_data["candidates"]

    if isinstance(raw_data.get("data"), list):
        return raw_data["data"]

    raise ExternalJSONProviderError(
        "External JSON object must contain a list field named "
        "'results', 'candidates', or 'data'."
    )


def normalize_json_item(item, index):
    """
    Normalize one JSON object into a raw candidate dictionary.

    Args:
        item: Raw JSON item.
        index: 1-based item index for error messages.

    Returns:
        dict: Normalized raw candidate dictionary.

    Raises:
        ExternalJSONProviderError: If the item is invalid.
    """
    if not isinstance(item, dict):
        raise ExternalJSONProviderError(
            f"External JSON item {index} must be an object."
        )

    normalized_item = {}

    for field in REQUIRED_FIELDS:
        value = item.get(field, "")

        if value is None:
            value = ""

        normalized_item[field] = str(value).strip()

    if not normalized_item["source"]:
        normalized_item["source"] = SOURCE_NAME

    if not normalized_item["isin"]:
        raise ExternalJSONProviderError(
            f"External JSON item {index} is invalid because ISIN is empty."
        )

    if not normalized_item["name"]:
        raise ExternalJSONProviderError(
            f"External JSON item {index} is invalid because name is empty."
        )

    return normalized_item