"""
Provider health and configuration status for Discover Bonds.

The Discover Bonds page currently supports two data flows:

1. CSV Provider
   The backend reads a local CSV universe after the user uploads it.

2. AI Research Provider
   The frontend uses Puter.js with web search to generate structured JSON.
   The backend validates/imports that JSON and calculates missing YTM/duration
   when enough verified inputs exist.

This module returns safe read-only status information. It does not run
discovery and it does not create records.
"""

import csv
from pathlib import Path

from django.utils import timezone

from bonds.discovery.providers import csv_provider
from bonds.discovery.providers.provider_registry import (
    DEFAULT_DISCOVERY_SOURCE,
    get_supported_provider_names,
)


AI_RESEARCH_SOURCE = "ai_research_agent"


def get_provider_status_report():
    """
    Build a provider/workflow status report for the frontend.

    Returns:
        dict: Safe provider status payload.
    """
    return {
        "generated_at": timezone.now(),
        "default_source": DEFAULT_DISCOVERY_SOURCE,
        "supported_sources": [
            *get_supported_provider_names(),
            AI_RESEARCH_SOURCE,
        ],
        "providers": [
            get_csv_provider_status(),
            get_ai_research_provider_status(),
        ],
    }


def get_csv_provider_status():
    """
    Return status for the CSV Provider.

    Returns:
        dict: CSV Provider status.
    """
    csv_file_path = Path(csv_provider.CSV_FILE_PATH)

    if not csv_file_path.exists():
        return {
            "source": csv_provider.get_provider_name(),
            "label": "CSV Provider",
            "available": False,
            "mode": "uploaded_csv_file",
            "detail": "No CSV bond universe file has been uploaded yet.",
            "candidate_count": 0,
            "file_exists": False,
            "file_name": csv_file_path.name,
            "configuration": {
                "required_columns": csv_provider.REQUIRED_COLUMNS,
                "optional_columns": csv_provider.OPTIONAL_COLUMNS,
                "missing_columns": csv_provider.REQUIRED_COLUMNS,
            },
        }

    try:
        row_count, missing_columns = inspect_csv_file(csv_file_path)

        return {
            "source": csv_provider.get_provider_name(),
            "label": "CSV Provider",
            "available": len(missing_columns) == 0,
            "mode": "uploaded_csv_file",
            "detail": (
                "CSV file is available."
                if len(missing_columns) == 0
                else "CSV file is missing required columns."
            ),
            "candidate_count": row_count,
            "file_exists": True,
            "file_name": csv_file_path.name,
            "configuration": {
                "required_columns": csv_provider.REQUIRED_COLUMNS,
                "optional_columns": csv_provider.OPTIONAL_COLUMNS,
                "missing_columns": missing_columns,
            },
        }
    except Exception as exc:
        return {
            "source": csv_provider.get_provider_name(),
            "label": "CSV Provider",
            "available": False,
            "mode": "uploaded_csv_file",
            "detail": str(exc),
            "candidate_count": 0,
            "file_exists": True,
            "file_name": csv_file_path.name,
            "configuration": {
                "required_columns": csv_provider.REQUIRED_COLUMNS,
                "optional_columns": csv_provider.OPTIONAL_COLUMNS,
                "missing_columns": [],
            },
        }


def get_ai_research_provider_status():
    """
    Return status for the AI Research Provider workflow.

    Returns:
        dict: AI Research Provider status.
    """
    return {
        "source": AI_RESEARCH_SOURCE,
        "label": "AI Research Provider",
        "available": True,
        "mode": "puter_frontend_web_search",
        "detail": (
            "AI research is generated through Puter.js in the frontend and "
            "then validated/imported by the Django backend."
        ),
        "candidate_count": None,
        "file_exists": None,
        "file_name": None,
        "configuration": {
            "backend_openai_client": False,
            "uses_frontend_puter_js": True,
            "backend_import_endpoint": "/api/ai-research/import-discovery/",
            "backend_calculates_missing_ytm_duration": True,
        },
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
