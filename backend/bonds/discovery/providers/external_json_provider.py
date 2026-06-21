"""
External JSON provider for the Bond Discovery Engine.

This provider can load discovered bond candidates from:

1. A configured external JSON API, if:
       BOND_DISCOVERY_EXTERNAL_API_URL is set

2. A local fallback JSON file, if no API URL is configured:
       backend/bonds/discovery/data/external_bond_universe.json

It also supports flexible response mapping through:
    bonds.discovery.providers.external_response_mapper

Important:
    This provider only loads and maps raw dictionaries.

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
from bonds.discovery.providers.external_response_mapper import (
    ExternalResponseMapperError,
    normalize_external_response,
)


SOURCE_NAME = "external_json_provider"

JSON_FILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "external_bond_universe.json"
)


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
        ExternalJSONProviderError: If data cannot be loaded or mapped.
    """
    if external_api_is_configured():
        raw_data = load_candidates_from_external_api()
    else:
        raw_data = load_candidates_from_local_json()

    try:
        return normalize_external_response(
            raw_data=raw_data,
            source_name=SOURCE_NAME,
        )
    except ExternalResponseMapperError as exc:
        raise ExternalJSONProviderError(str(exc)) from exc


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