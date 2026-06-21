"""
Safe external API client for the Bond Discovery Engine.

This module prepares the application for real external bond data providers.

It is intentionally generic:
- It reads configuration from environment variables.
- It uses only Python standard library modules.
- It does not depend on a specific paid provider.
- It expects JSON data from the configured endpoint.
- It does not perform investment filtering.

The discovery provider remains responsible only for loading raw candidates.
The discovery service remains responsible for:
- validation
- maturity filtering
- rating filtering
- duplicate checks
- Watchlist/Portfolio exclusion

Environment variables:
    BOND_DISCOVERY_EXTERNAL_API_URL
    BOND_DISCOVERY_EXTERNAL_API_KEY
    BOND_DISCOVERY_EXTERNAL_API_TIMEOUT
    BOND_DISCOVERY_EXTERNAL_API_AUTH_HEADER
    BOND_DISCOVERY_EXTERNAL_API_AUTH_PREFIX
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 15


class ExternalAPIClientError(Exception):
    """
    Raised when the external API client cannot fetch or decode data.
    """


def get_external_api_url():
    """
    Return the configured external API URL.

    Returns:
        str: API URL or empty string.
    """
    return os.getenv("BOND_DISCOVERY_EXTERNAL_API_URL", "").strip()


def get_external_api_key():
    """
    Return the configured external API key.

    Returns:
        str: API key or empty string.
    """
    return os.getenv("BOND_DISCOVERY_EXTERNAL_API_KEY", "").strip()


def get_external_api_timeout():
    """
    Return the configured timeout in seconds.

    Returns:
        int: Timeout seconds.
    """
    raw_timeout = os.getenv(
        "BOND_DISCOVERY_EXTERNAL_API_TIMEOUT",
        str(DEFAULT_TIMEOUT_SECONDS),
    ).strip()

    try:
        timeout = int(raw_timeout)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS

    if timeout <= 0:
        return DEFAULT_TIMEOUT_SECONDS

    return timeout


def get_auth_header_name():
    """
    Return the configured authentication header name.

    Returns:
        str: Header name.
    """
    return os.getenv(
        "BOND_DISCOVERY_EXTERNAL_API_AUTH_HEADER",
        "Authorization",
    ).strip() or "Authorization"


def get_auth_header_prefix():
    """
    Return the configured authentication prefix.

    Returns:
        str: Header prefix.
    """
    return os.getenv(
        "BOND_DISCOVERY_EXTERNAL_API_AUTH_PREFIX",
        "Bearer",
    ).strip()


def external_api_is_configured():
    """
    Check whether an external API URL is configured.

    Returns:
        bool: True if URL exists.
    """
    return bool(get_external_api_url())


def build_request_headers():
    """
    Build HTTP headers for the external API request.

    Returns:
        dict: HTTP headers.
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "BondAnalysisDashboard/1.0",
    }

    api_key = get_external_api_key()

    if api_key:
        auth_header_name = get_auth_header_name()
        auth_header_prefix = get_auth_header_prefix()

        if auth_header_prefix:
            headers[auth_header_name] = f"{auth_header_prefix} {api_key}"
        else:
            headers[auth_header_name] = api_key

    return headers


def fetch_external_json_data():
    """
    Fetch JSON data from the configured external API.

    Returns:
        object: Parsed JSON response.

    Raises:
        ExternalAPIClientError: If URL is missing, request fails, or JSON is invalid.
    """
    api_url = get_external_api_url()

    if not api_url:
        raise ExternalAPIClientError(
            "External API URL is not configured."
        )

    request = Request(
        url=api_url,
        headers=build_request_headers(),
        method="GET",
    )

    try:
        with urlopen(request, timeout=get_external_api_timeout()) as response:
            raw_body = response.read()
    except HTTPError as exc:
        raise ExternalAPIClientError(
            f"External API returned HTTP error {exc.code}."
        ) from exc
    except URLError as exc:
        raise ExternalAPIClientError(
            f"External API request failed: {exc.reason}."
        ) from exc
    except TimeoutError as exc:
        raise ExternalAPIClientError(
            "External API request timed out."
        ) from exc

    if not raw_body:
        raise ExternalAPIClientError(
            "External API returned an empty response."
        )

    try:
        decoded_body = raw_body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExternalAPIClientError(
            "External API response must be UTF-8 encoded JSON."
        ) from exc

    try:
        return json.loads(decoded_body)
    except json.JSONDecodeError as exc:
        raise ExternalAPIClientError(
            "External API response contains invalid JSON."
        ) from exc