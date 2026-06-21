"""
Provider health and configuration status for the Bond Discovery Engine.

This module gives the frontend a safe read-only status report about available
discovery providers.

It does not run full discovery and it does not add candidates to the database.

The report helps the user understand:
- which providers are available
- whether the CSV file exists
- how many rows the CSV file contains
- whether the external JSON provider uses local fallback or API mode
- whether external API URL/API key are configured

Sensitive values such as API keys are never returned.
"""

import csv
from pathlib import Path
from urllib.parse import urlparse

from django.utils import timezone

from bonds.discovery.providers import (
    csv_provider,
    external_json_provider,
    static_provider,
)
from bonds.discovery.providers.external_api_client import (
    external_api_is_configured,
    get_auth_header_name,
    get_external_api_key,
    get_external_api_timeout,
    get_external_api_url,
)
from bonds.discovery.providers.provider_registry import (
    DEFAULT_DISCOVERY_SOURCE,
    get_supported_provider_names,
)


def get_provider_status_report():
    """
    Build a safe provider status report.

    Returns:
        dict: Provider status report.
    """
    return {
        "generated_at": timezone.now().isoformat(),
        "default_source": DEFAULT_DISCOVERY_SOURCE,
        "supported_sources": get_supported_provider_names(),
        "providers": [
            build_static_provider_status(),
            build_csv_provider_status(),
            build_external_json_provider_status(),
        ],
    }


def build_static_provider_status():
    """
    Build status for the static provider.

    Returns:
        dict: Static provider status.
    """
    try:
        candidates = static_provider.load_candidates()

        return {
            "source": static_provider.get_provider_name(),
            "label": "Static Provider",
            "available": True,
            "mode": "local_static_data",
            "detail": "Static demo provider is available.",
            "candidate_count": len(candidates),
            "file_exists": None,
            "file_name": None,
            "configuration": {},
        }
    except Exception as exc:
        return {
            "source": "static_provider",
            "label": "Static Provider",
            "available": False,
            "mode": "local_static_data",
            "detail": str(exc),
            "candidate_count": 0,
            "file_exists": None,
            "file_name": None,
            "configuration": {},
        }


def build_csv_provider_status():
    """
    Build status for the CSV provider.

    Returns:
        dict: CSV provider status.
    """
    csv_file_path = Path(csv_provider.CSV_FILE_PATH)

    if not csv_file_path.exists():
        return {
            "source": csv_provider.get_provider_name(),
            "label": "CSV Provider",
            "available": False,
            "mode": "local_csv_file",
            "detail": "CSV file does not exist.",
            "candidate_count": 0,
            "file_exists": False,
            "file_name": csv_file_path.name,
            "configuration": {
                "required_columns": csv_provider.REQUIRED_COLUMNS,
            },
        }

    try:
        row_count, missing_columns = inspect_csv_file(csv_file_path)

        if missing_columns:
            return {
                "source": csv_provider.get_provider_name(),
                "label": "CSV Provider",
                "available": False,
                "mode": "local_csv_file",
                "detail": (
                    "CSV file exists but is missing required columns: "
                    f"{', '.join(missing_columns)}."
                ),
                "candidate_count": row_count,
                "file_exists": True,
                "file_name": csv_file_path.name,
                "configuration": {
                    "required_columns": csv_provider.REQUIRED_COLUMNS,
                },
            }

        return {
            "source": csv_provider.get_provider_name(),
            "label": "CSV Provider",
            "available": True,
            "mode": "local_csv_file",
            "detail": "CSV provider is available.",
            "candidate_count": row_count,
            "file_exists": True,
            "file_name": csv_file_path.name,
            "configuration": {
                "required_columns": csv_provider.REQUIRED_COLUMNS,
            },
        }
    except Exception as exc:
        return {
            "source": csv_provider.get_provider_name(),
            "label": "CSV Provider",
            "available": False,
            "mode": "local_csv_file",
            "detail": str(exc),
            "candidate_count": 0,
            "file_exists": True,
            "file_name": csv_file_path.name,
            "configuration": {
                "required_columns": csv_provider.REQUIRED_COLUMNS,
            },
        }


def build_external_json_provider_status():
    """
    Build status for the external JSON provider.

    Returns:
        dict: External JSON provider status.
    """
    api_url = get_external_api_url()
    api_configured = external_api_is_configured()
    api_key_configured = bool(get_external_api_key())

    configuration = {
        "external_api_url_configured": api_configured,
        "external_api_host": extract_host_from_url(api_url),
        "external_api_key_configured": api_key_configured,
        "external_api_timeout_seconds": get_external_api_timeout(),
        "external_api_auth_header": get_auth_header_name(),
    }

    if api_configured:
        return {
            "source": external_json_provider.get_provider_name(),
            "label": "External JSON Provider",
            "available": True,
            "mode": "external_api",
            "detail": (
                "External API URL is configured. Connectivity is checked "
                "when discovery runs."
            ),
            "candidate_count": None,
            "file_exists": None,
            "file_name": None,
            "configuration": configuration,
        }

    json_file_path = Path(external_json_provider.JSON_FILE_PATH)

    if not json_file_path.exists():
        return {
            "source": external_json_provider.get_provider_name(),
            "label": "External JSON Provider",
            "available": False,
            "mode": "local_json_fallback",
            "detail": "External API URL is empty and local JSON fallback file does not exist.",
            "candidate_count": 0,
            "file_exists": False,
            "file_name": json_file_path.name,
            "configuration": configuration,
        }

    try:
        candidates = external_json_provider.load_candidates()

        return {
            "source": external_json_provider.get_provider_name(),
            "label": "External JSON Provider",
            "available": True,
            "mode": "local_json_fallback",
            "detail": "Using local JSON fallback file.",
            "candidate_count": len(candidates),
            "file_exists": True,
            "file_name": json_file_path.name,
            "configuration": configuration,
        }
    except Exception as exc:
        return {
            "source": external_json_provider.get_provider_name(),
            "label": "External JSON Provider",
            "available": False,
            "mode": "local_json_fallback",
            "detail": str(exc),
            "candidate_count": 0,
            "file_exists": True,
            "file_name": json_file_path.name,
            "configuration": configuration,
        }


def inspect_csv_file(csv_file_path):
    """
    Inspect the CSV provider file.

    Args:
        csv_file_path: Path to CSV file.

    Returns:
        tuple[int, list[str]]: Row count and missing required columns.
    """
    with csv_file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []

        missing_columns = [
            column
            for column in csv_provider.REQUIRED_COLUMNS
            if column not in fieldnames
        ]

        row_count = 0

        for row in reader:
            if row_has_data(row):
                row_count += 1

    return row_count, missing_columns


def row_has_data(row):
    """
    Check whether a CSV row has at least one non-empty value.

    Args:
        row: CSV row dictionary.

    Returns:
        bool: True if row has data.
    """
    return any(
        value is not None and str(value).strip()
        for value in row.values()
    )


def extract_host_from_url(url):
    """
    Extract host from URL without exposing full URL details.

    Args:
        url: Raw URL.

    Returns:
        str: Host name or empty string.
    """
    if not url:
        return ""

    parsed_url = urlparse(url)

    return parsed_url.netloc