"""
JSON schemas and lightweight validators for AI bond research.

This module defines the structured JSON format that the AI Research Agent must
return before the application imports any researched bond data.

Important design rules:
- AI-researched data is not treated as an official live market feed.
- Every imported record must keep source information.
- Every imported record must keep confidence and review status.
- Missing values must be represented as None/null, not guessed values.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}
REVIEW_STATUSES = {"NEEDS_REVIEW", "REVIEWED", "REJECTED"}
RESEARCH_SOURCE_TYPES = {
    "OFFICIAL_ISSUER",
    "EXCHANGE",
    "REGULATOR",
    "BROKER",
    "DATA_VENDOR",
    "NEWS",
    "OTHER",
}


DISCOVERY_RESEARCH_RESULT_SCHEMA: dict[str, Any] = {
    "name": "discovery_research_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "research_type",
            "query_summary",
            "filters",
            "retrieved_at",
            "items",
            "warnings",
        ],
        "properties": {
            "research_type": {
                "type": "string",
                "enum": ["DISCOVERY"],
            },
            "query_summary": {
                "type": "string",
            },
            "filters": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "countries",
                    "currencies",
                    "minimum_rating",
                    "maturity_from",
                    "maturity_to",
                    "issuer_types",
                    "bond_types",
                ],
                "properties": {
                    "countries": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "currencies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "minimum_rating": {
                        "type": ["string", "null"],
                    },
                    "maturity_from": {
                        "type": ["string", "null"],
                    },
                    "maturity_to": {
                        "type": ["string", "null"],
                    },
                    "issuer_types": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "bond_types": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            "retrieved_at": {
                "type": "string",
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "isin",
                        "name",
                        "issuer",
                        "country",
                        "currency",
                        "coupon_rate",
                        "maturity_date",
                        "credit_rating",
                        "rating_source",
                        "bond_type",
                        "seniority",
                        "coupon_frequency",
                        "market_price",
                        "ytm",
                        "duration",
                        "primary_source_name",
                        "primary_source_url",
                        "sources",
                        "retrieved_at",
                        "confidence",
                        "needs_review",
                        "review_status",
                        "research_notes",
                        "missing_fields",
                    ],
                    "properties": {
                        "isin": {"type": "string"},
                        "name": {"type": "string"},
                        "issuer": {"type": "string"},
                        "country": {"type": "string"},
                        "currency": {"type": "string"},
                        "coupon_rate": {"type": ["string", "number", "null"]},
                        "maturity_date": {"type": ["string", "null"]},
                        "credit_rating": {"type": ["string", "null"]},
                        "rating_source": {"type": ["string", "null"]},
                        "bond_type": {"type": ["string", "null"]},
                        "seniority": {"type": ["string", "null"]},
                        "coupon_frequency": {"type": ["integer", "null"]},
                        "market_price": {"type": ["string", "number", "null"]},
                        "ytm": {"type": ["string", "number", "null"]},
                        "duration": {"type": ["string", "number", "null"]},
                        "primary_source_name": {"type": "string"},
                        "primary_source_url": {"type": "string"},
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": [
                                    "source_name",
                                    "source_url",
                                    "source_type",
                                    "fields_supported",
                                    "notes",
                                ],
                                "properties": {
                                    "source_name": {"type": "string"},
                                    "source_url": {"type": "string"},
                                    "source_type": {
                                        "type": "string",
                                        "enum": sorted(RESEARCH_SOURCE_TYPES),
                                    },
                                    "fields_supported": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "notes": {"type": "string"},
                                },
                            },
                        },
                        "retrieved_at": {"type": "string"},
                        "confidence": {
                            "type": "string",
                            "enum": sorted(CONFIDENCE_LEVELS),
                        },
                        "needs_review": {"type": "boolean"},
                        "review_status": {
                            "type": "string",
                            "enum": sorted(REVIEW_STATUSES),
                        },
                        "research_notes": {"type": "string"},
                        "missing_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "warnings": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}


BOND_MARKET_RESEARCH_RESULT_SCHEMA: dict[str, Any] = {
    "name": "bond_market_research_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "research_type",
            "query_summary",
            "requested_isins",
            "retrieved_at",
            "items",
            "warnings",
        ],
        "properties": {
            "research_type": {
                "type": "string",
                "enum": ["MARKET_REFRESH"],
            },
            "query_summary": {
                "type": "string",
            },
            "requested_isins": {
                "type": "array",
                "items": {"type": "string"},
            },
            "retrieved_at": {
                "type": "string",
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "isin",
                        "name",
                        "issuer",
                        "currency",
                        "quote_date",
                        "market_price",
                        "ytm",
                        "market_required_return",
                        "bid_price",
                        "ask_price",
                        "credit_rating",
                        "rating_source",
                        "primary_source_name",
                        "primary_source_url",
                        "sources",
                        "retrieved_at",
                        "confidence",
                        "needs_review",
                        "review_status",
                        "research_notes",
                        "missing_fields",
                    ],
                    "properties": {
                        "isin": {"type": "string"},
                        "name": {"type": ["string", "null"]},
                        "issuer": {"type": ["string", "null"]},
                        "currency": {"type": ["string", "null"]},
                        "quote_date": {"type": ["string", "null"]},
                        "market_price": {"type": ["string", "number", "null"]},
                        "ytm": {"type": ["string", "number", "null"]},
                        "market_required_return": {
                            "type": ["string", "number", "null"],
                        },
                        "bid_price": {"type": ["string", "number", "null"]},
                        "ask_price": {"type": ["string", "number", "null"]},
                        "credit_rating": {"type": ["string", "null"]},
                        "rating_source": {"type": ["string", "null"]},
                        "primary_source_name": {"type": "string"},
                        "primary_source_url": {"type": "string"},
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": [
                                    "source_name",
                                    "source_url",
                                    "source_type",
                                    "fields_supported",
                                    "notes",
                                ],
                                "properties": {
                                    "source_name": {"type": "string"},
                                    "source_url": {"type": "string"},
                                    "source_type": {
                                        "type": "string",
                                        "enum": sorted(RESEARCH_SOURCE_TYPES),
                                    },
                                    "fields_supported": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "notes": {"type": "string"},
                                },
                            },
                        },
                        "retrieved_at": {"type": "string"},
                        "confidence": {
                            "type": "string",
                            "enum": sorted(CONFIDENCE_LEVELS),
                        },
                        "needs_review": {"type": "boolean"},
                        "review_status": {
                            "type": "string",
                            "enum": sorted(REVIEW_STATUSES),
                        },
                        "research_notes": {"type": "string"},
                        "missing_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "warnings": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}


def validate_discovery_research_result(payload: dict[str, Any]) -> list[str]:
    """
    Validate the minimum business rules for a discovery research result.

    This validator intentionally does not replace JSON Schema validation.
    It checks project-specific rules that are important before import.

    Args:
        payload: Parsed JSON payload returned by the AI Research Agent.

    Returns:
        A list of validation error messages. Empty list means valid enough for
        the next import step.
    """
    errors: list[str] = []

    if payload.get("research_type") != "DISCOVERY":
        errors.append("research_type must be DISCOVERY.")

    _validate_iso_datetime(payload.get("retrieved_at"), "retrieved_at", errors)

    items = payload.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list.")
        return errors

    for index, item in enumerate(items):
        prefix = f"items[{index}]"

        _validate_required_string(item, "isin", prefix, errors)
        _validate_required_string(item, "name", prefix, errors)
        _validate_required_string(item, "issuer", prefix, errors)
        _validate_required_string(item, "currency", prefix, errors)
        _validate_required_string(item, "primary_source_name", prefix, errors)
        _validate_required_string(item, "primary_source_url", prefix, errors)

        _validate_confidence(item, prefix, errors)
        _validate_review_status(item, prefix, errors)
        _validate_iso_datetime(item.get("retrieved_at"), f"{prefix}.retrieved_at", errors)

        _validate_optional_decimal(item, "coupon_rate", prefix, errors)
        _validate_optional_decimal(item, "market_price", prefix, errors)
        _validate_optional_decimal(item, "ytm", prefix, errors)
        _validate_optional_decimal(item, "duration", prefix, errors)

        _validate_sources(item, prefix, errors)

    return errors


def validate_market_research_result(payload: dict[str, Any]) -> list[str]:
    """
    Validate the minimum business rules for a market refresh research result.

    Args:
        payload: Parsed JSON payload returned by the AI Research Agent.

    Returns:
        A list of validation error messages. Empty list means valid enough for
        the next import step.
    """
    errors: list[str] = []

    if payload.get("research_type") != "MARKET_REFRESH":
        errors.append("research_type must be MARKET_REFRESH.")

    _validate_iso_datetime(payload.get("retrieved_at"), "retrieved_at", errors)

    items = payload.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list.")
        return errors

    for index, item in enumerate(items):
        prefix = f"items[{index}]"

        _validate_required_string(item, "isin", prefix, errors)
        _validate_required_string(item, "primary_source_name", prefix, errors)
        _validate_required_string(item, "primary_source_url", prefix, errors)

        _validate_confidence(item, prefix, errors)
        _validate_review_status(item, prefix, errors)
        _validate_iso_datetime(item.get("retrieved_at"), f"{prefix}.retrieved_at", errors)

        _validate_optional_decimal(item, "market_price", prefix, errors)
        _validate_optional_decimal(item, "ytm", prefix, errors)
        _validate_optional_decimal(item, "market_required_return", prefix, errors)
        _validate_optional_decimal(item, "bid_price", prefix, errors)
        _validate_optional_decimal(item, "ask_price", prefix, errors)

        _validate_sources(item, prefix, errors)

    return errors


def _validate_required_string(
    item: dict[str, Any],
    field_name: str,
    prefix: str,
    errors: list[str],
) -> None:
    """
    Validate that a field exists and is a non-empty string.
    """
    value = item.get(field_name)

    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}.{field_name} must be a non-empty string.")


def _validate_optional_decimal(
    item: dict[str, Any],
    field_name: str,
    prefix: str,
    errors: list[str],
) -> None:
    """
    Validate that an optional numeric field can be parsed as Decimal.
    """
    value = item.get(field_name)

    if value in (None, ""):
        return

    try:
        Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"{prefix}.{field_name} must be numeric or null.")


def _validate_confidence(
    item: dict[str, Any],
    prefix: str,
    errors: list[str],
) -> None:
    """
    Validate confidence enum.
    """
    confidence = item.get("confidence")

    if confidence not in CONFIDENCE_LEVELS:
        errors.append(
            f"{prefix}.confidence must be one of: "
            f"{', '.join(sorted(CONFIDENCE_LEVELS))}."
        )


def _validate_review_status(
    item: dict[str, Any],
    prefix: str,
    errors: list[str],
) -> None:
    """
    Validate review status enum.
    """
    review_status = item.get("review_status")

    if review_status not in REVIEW_STATUSES:
        errors.append(
            f"{prefix}.review_status must be one of: "
            f"{', '.join(sorted(REVIEW_STATUSES))}."
        )


def _validate_iso_datetime(
    value: Any,
    field_name: str,
    errors: list[str],
) -> None:
    """
    Validate that a datetime string is ISO-like.

    The function accepts a trailing Z by converting it to +00:00.
    """
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field_name} must be a non-empty ISO datetime string.")
        return

    normalized_value = value.replace("Z", "+00:00")

    try:
        datetime.fromisoformat(normalized_value)
    except ValueError:
        errors.append(f"{field_name} must be a valid ISO datetime string.")


def _validate_sources(
    item: dict[str, Any],
    prefix: str,
    errors: list[str],
) -> None:
    """
    Validate source list for one researched item.
    """
    sources = item.get("sources")

    if not isinstance(sources, list) or not sources:
        errors.append(f"{prefix}.sources must contain at least one source.")
        return

    for source_index, source in enumerate(sources):
        source_prefix = f"{prefix}.sources[{source_index}]"

        _validate_required_string(source, "source_name", source_prefix, errors)
        _validate_required_string(source, "source_url", source_prefix, errors)

        source_type = source.get("source_type")
        if source_type not in RESEARCH_SOURCE_TYPES:
            errors.append(
                f"{source_prefix}.source_type must be one of: "
                f"{', '.join(sorted(RESEARCH_SOURCE_TYPES))}."
            )

        fields_supported = source.get("fields_supported")
        if not isinstance(fields_supported, list) or not fields_supported:
            errors.append(
                f"{source_prefix}.fields_supported must contain at least one field."
            )