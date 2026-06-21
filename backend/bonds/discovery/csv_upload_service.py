"""
CSV upload service for the Bond Discovery Engine.

This module validates and stores an uploaded CSV bond universe file.

The uploaded CSV replaces:
    backend/bonds/discovery/data/bond_universe.csv

Safety rules:
- The old CSV file is not replaced until the new file is validated.
- Required columns must exist.
- Rows must be readable by the existing CSV provider logic.
- Empty rows are ignored.
- The uploaded file must not exceed the configured size limit.

This service does not run discovery automatically. It only updates the CSV
source file used later by csv_provider.
"""

import csv
import io
from pathlib import Path

from bonds.discovery.providers.csv_provider import (
    CSV_FILE_PATH,
    REQUIRED_COLUMNS,
    CSVProviderError,
    normalize_csv_row,
    validate_csv_headers,
)


MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024


class CSVUploadError(Exception):
    """
    Raised when an uploaded CSV file is invalid.
    """


def validate_and_store_uploaded_csv(uploaded_file):
    """
    Validate and store an uploaded CSV file.

    Args:
        uploaded_file: Django UploadedFile instance.

    Returns:
        dict: Upload summary.

    Raises:
        CSVUploadError: If validation fails.
    """
    validate_uploaded_file_metadata(uploaded_file)

    raw_bytes = uploaded_file.read()

    if not raw_bytes:
        raise CSVUploadError("Uploaded CSV file is empty.")

    csv_text = decode_csv_bytes(raw_bytes)
    row_count = validate_csv_content(csv_text)

    store_csv_content(csv_text)

    return {
        "filename": uploaded_file.name,
        "stored_path": str(CSV_FILE_PATH),
        "row_count": row_count,
        "required_columns": REQUIRED_COLUMNS,
    }


def validate_uploaded_file_metadata(uploaded_file):
    """
    Validate file metadata before reading content.

    Args:
        uploaded_file: Django UploadedFile instance.

    Raises:
        CSVUploadError: If file metadata is invalid.
    """
    if uploaded_file is None:
        raise CSVUploadError("CSV file is required.")

    filename = uploaded_file.name or ""

    if not filename.lower().endswith(".csv"):
        raise CSVUploadError("Only .csv files are allowed.")

    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        max_size_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)

        raise CSVUploadError(
            f"CSV file is too large. Maximum allowed size is {max_size_mb:.0f} MB."
        )


def decode_csv_bytes(raw_bytes):
    """
    Decode raw CSV bytes.

    Args:
        raw_bytes: Uploaded file bytes.

    Returns:
        str: Decoded CSV text.

    Raises:
        CSVUploadError: If decoding fails.
    """
    try:
        return raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVUploadError(
            "CSV file must be encoded as UTF-8 or UTF-8 with BOM."
        ) from exc


def validate_csv_content(csv_text):
    """
    Validate CSV headers and rows.

    Args:
        csv_text: Decoded CSV text.

    Returns:
        int: Number of valid non-empty rows.

    Raises:
        CSVUploadError: If the CSV is invalid.
    """
    csv_stream = io.StringIO(csv_text)
    reader = csv.DictReader(csv_stream)

    try:
        validate_csv_headers(reader.fieldnames)
    except CSVProviderError as exc:
        raise CSVUploadError(str(exc)) from exc

    row_count = 0

    for row_number, row in enumerate(reader, start=2):
        if row_is_empty(row):
            continue

        try:
            normalize_csv_row(row=row, row_number=row_number)
        except CSVProviderError as exc:
            raise CSVUploadError(str(exc)) from exc

        row_count += 1

    if row_count == 0:
        raise CSVUploadError("CSV file must contain at least one valid row.")

    return row_count


def row_is_empty(row):
    """
    Check whether a CSV row is completely empty.

    Args:
        row: CSV row dictionary.

    Returns:
        bool: True if all values are empty.
    """
    if not row:
        return True

    return all((value is None or str(value).strip() == "") for value in row.values())


def store_csv_content(csv_text):
    """
    Store validated CSV content atomically.

    Args:
        csv_text: Validated CSV text.
    """
    csv_path = Path(CSV_FILE_PATH)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = csv_path.with_suffix(".csv.tmp")

    temporary_path.write_text(csv_text, encoding="utf-8", newline="")

    temporary_path.replace(csv_path)