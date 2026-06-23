"""
CSV provider for the Bond Discovery Engine.

This provider reads discovered bond candidates from a local CSV file.

The CSV provider is useful as an MVP bridge before connecting to a paid or
official market data API. It allows the application to import a bond universe
from a controlled file without hardcoding candidate data in Python code.

Expected CSV location:
    backend/bonds/discovery/data/bond_universe.csv

Expected required columns:
    isin
    name
    issuer
    country
    currency
    coupon_rate
    maturity_date
    credit_rating
    rating_source
    market_price
    ytm
    duration
    source
    source_url

Optional columns:
    bond_type
    coupon_frequency

Important:
    This provider does not validate investment rules.
    It only loads raw candidate dictionaries.

Validation, rating filtering, maturity filtering, duplicate checks and
Watchlist/Portfolio exclusion remain inside discovery_service.py.
"""

import csv
from pathlib import Path


SOURCE_NAME = "csv_provider"

CSV_FILE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "bond_universe.csv"
)

REQUIRED_COLUMNS = [
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

OPTIONAL_COLUMNS = [
    "bond_type",
    "coupon_frequency",
]


class CSVProviderError(Exception):
    """
    Raised when the CSV provider cannot load candidate data.
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
    Load raw bond candidates from the configured CSV file.

    Returns:
        list[dict]: Raw candidate dictionaries.

    Raises:
        CSVProviderError: If the CSV file is missing or invalid.
    """
    if not CSV_FILE_PATH.exists():
        raise CSVProviderError(
            f"CSV discovery file was not found: {CSV_FILE_PATH}"
        )

    with CSV_FILE_PATH.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        validate_csv_headers(reader.fieldnames)

        candidates = []

        for row_number, row in enumerate(reader, start=2):
            normalized_row = normalize_csv_row(row=row, row_number=row_number)
            candidates.append(normalized_row)

    return candidates


def validate_csv_headers(fieldnames):
    """
    Validate that the CSV file contains all required columns.

    Args:
        fieldnames: Header names returned by csv.DictReader.

    Raises:
        CSVProviderError: If one or more required columns are missing.
    """
    if not fieldnames:
        raise CSVProviderError("CSV discovery file has no header row.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in fieldnames
    ]

    if missing_columns:
        missing_text = ", ".join(missing_columns)

        raise CSVProviderError(
            f"CSV discovery file is missing required columns: {missing_text}"
        )


def normalize_csv_row(row, row_number):
    """
    Normalize one CSV row into a raw candidate dictionary.

    Args:
        row: Raw CSV row.
        row_number: CSV row number for error messages.

    Returns:
        dict: Normalized raw candidate dictionary.
    """
    normalized_row = {}

    for column in [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]:
        value = row.get(column, "")

        if value is None:
            value = ""

        normalized_row[column] = value.strip()

    if not normalized_row["source"]:
        normalized_row["source"] = SOURCE_NAME

    if not normalized_row["isin"]:
        raise CSVProviderError(
            f"CSV row {row_number} is invalid because ISIN is empty."
        )

    if not normalized_row["name"]:
        raise CSVProviderError(
            f"CSV row {row_number} is invalid because name is empty."
        )

    return normalized_row


