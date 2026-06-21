"""
External API response mapper for the Bond Discovery Engine.

This module converts external JSON responses into the canonical candidate
dictionary format expected by discovery_service.py.

Why this exists:
    Different providers use different field names.

Example provider fields:
    securityId, bondName, issuerName, maturity, rating, price

Canonical app fields:
    isin, name, issuer, maturity_date, credit_rating, market_price

This mapper keeps provider-specific response shapes away from the discovery
service. The discovery service receives normalized raw dictionaries and remains
responsible for validation, filtering, duplicate checks, and Watchlist logic.

Optional environment variable:
    BOND_DISCOVERY_EXTERNAL_API_FIELD_MAP

Example value:
    {
      "isin": ["securityId", "isin"],
      "name": ["bondName", "name"],
      "issuer": ["issuerName", "issuer"],
      "maturity_date": ["maturity", "maturityDate"],
      "credit_rating": ["rating", "creditRating"],
      "market_price": ["price", "lastPrice"]
    }

The environment value is optional. If empty, built-in aliases are used.
"""

import json
import os


CANONICAL_FIELDS = [
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
    "ai_summary",
    "ai_reasoning",
]

REQUIRED_CANONICAL_FIELDS = [
    "isin",
    "name",
    "issuer",
    "currency",
    "coupon_rate",
    "maturity_date",
    "credit_rating",
]

DEFAULT_FIELD_ALIASES = {
    "isin": [
        "isin",
        "ISIN",
        "securityId",
        "security_id",
        "securityIdentifier",
        "security_identifier",
        "id",
    ],
    "name": [
        "name",
        "bondName",
        "bond_name",
        "securityName",
        "security_name",
        "description",
        "instrumentName",
        "instrument_name",
    ],
    "issuer": [
        "issuer",
        "issuerName",
        "issuer_name",
        "borrower",
        "obligor",
    ],
    "country": [
        "country",
        "countryCode",
        "country_code",
        "issuerCountry",
        "issuer_country",
    ],
    "currency": [
        "currency",
        "ccy",
        "currencyCode",
        "currency_code",
    ],
    "coupon_rate": [
        "coupon_rate",
        "couponRate",
        "coupon",
        "annualCouponRate",
        "annual_coupon_rate",
    ],
    "maturity_date": [
        "maturity_date",
        "maturityDate",
        "maturity",
        "redemptionDate",
        "redemption_date",
    ],
    "credit_rating": [
        "credit_rating",
        "creditRating",
        "rating",
        "ratingValue",
        "rating_value",
        "spRating",
        "s_and_p_rating",
        "snpRating",
    ],
    "rating_source": [
        "rating_source",
        "ratingSource",
        "ratingAgency",
        "rating_agency",
        "agency",
    ],
    "market_price": [
        "market_price",
        "marketPrice",
        "price",
        "lastPrice",
        "last_price",
        "cleanPrice",
        "clean_price",
    ],
    "ytm": [
        "ytm",
        "yieldToMaturity",
        "yield_to_maturity",
        "yield",
    ],
    "duration": [
        "duration",
        "modifiedDuration",
        "modified_duration",
        "durationYears",
        "duration_years",
    ],
    "source": [
        "source",
        "provider",
        "dataSource",
        "data_source",
    ],
    "source_url": [
        "source_url",
        "sourceUrl",
        "url",
        "link",
        "instrumentUrl",
        "instrument_url",
    ],
    "ai_summary": [
        "ai_summary",
        "summary",
        "providerSummary",
        "provider_summary",
    ],
    "ai_reasoning": [
        "ai_reasoning",
        "reasoning",
        "providerReasoning",
        "provider_reasoning",
    ],
}


class ExternalResponseMapperError(Exception):
    """
    Raised when an external JSON response cannot be mapped safely.
    """


def normalize_external_response(raw_data, source_name):
    """
    Normalize a parsed external JSON response into candidate dictionaries.

    Supported response formats:
        1. Direct list:
            [
                {"securityId": "..."}
            ]

        2. Wrapped response:
            {
                "results": [
                    {"securityId": "..."}
                ]
            }

        3. Wrapped response:
            {
                "candidates": [
                    {"securityId": "..."}
                ]
            }

        4. Wrapped response:
            {
                "data": [
                    {"securityId": "..."}
                ]
            }

    Args:
        raw_data: Parsed JSON response.
        source_name: Provider source name.

    Returns:
        list[dict]: Canonical candidate dictionaries.
    """
    candidate_items = extract_candidate_items(raw_data)
    candidates = []

    for index, item in enumerate(candidate_items, start=1):
        candidates.append(
            map_external_item_to_candidate(
                item=item,
                index=index,
                source_name=source_name,
            )
        )

    return candidates


def extract_candidate_items(raw_data):
    """
    Extract candidate items from a supported JSON response structure.

    Args:
        raw_data: Parsed JSON data.

    Returns:
        list: Candidate items.

    Raises:
        ExternalResponseMapperError: If format is unsupported.
    """
    if isinstance(raw_data, list):
        return raw_data

    if not isinstance(raw_data, dict):
        raise ExternalResponseMapperError(
            "External JSON data must be a list or an object containing candidates."
        )

    for key in ["results", "candidates", "data", "items", "securities"]:
        value = raw_data.get(key)

        if isinstance(value, list):
            return value

    raise ExternalResponseMapperError(
        "External JSON object must contain a list field named "
        "'results', 'candidates', 'data', 'items', or 'securities'."
    )


def map_external_item_to_candidate(item, index, source_name):
    """
    Map one external item into the canonical candidate format.

    Args:
        item: External JSON object.
        index: 1-based item index for error messages.
        source_name: Provider source name.

    Returns:
        dict: Canonical candidate dictionary.

    Raises:
        ExternalResponseMapperError: If the item is not an object.
    """
    if not isinstance(item, dict):
        raise ExternalResponseMapperError(
            f"External JSON item {index} must be an object."
        )

    field_aliases = build_effective_field_aliases()
    candidate = {}

    for canonical_field in CANONICAL_FIELDS:
        candidate[canonical_field] = resolve_field_value(
            item=item,
            aliases=field_aliases.get(canonical_field, [canonical_field]),
        )

    if not candidate["source"]:
        candidate["source"] = source_name

    if not candidate["rating_source"]:
        candidate["rating_source"] = "External JSON/API"

    return stringify_candidate_values(candidate)


def build_effective_field_aliases():
    """
    Build field aliases by combining defaults with optional env mapping.

    Returns:
        dict: Field aliases.
    """
    aliases = {
        field: list(DEFAULT_FIELD_ALIASES.get(field, [field]))
        for field in CANONICAL_FIELDS
    }

    custom_mapping = load_custom_field_mapping()

    for canonical_field, custom_aliases in custom_mapping.items():
        if canonical_field not in CANONICAL_FIELDS:
            continue

        aliases[canonical_field] = normalize_alias_list(
            custom_aliases,
            fallback=aliases[canonical_field],
        )

    return aliases


def load_custom_field_mapping():
    """
    Load optional provider field mapping from environment.

    Returns:
        dict: Custom mapping or empty dict.

    Raises:
        ExternalResponseMapperError: If mapping JSON is invalid.
    """
    raw_mapping = os.getenv(
        "BOND_DISCOVERY_EXTERNAL_API_FIELD_MAP",
        "",
    ).strip()

    if not raw_mapping:
        return {}

    try:
        mapping = json.loads(raw_mapping)
    except json.JSONDecodeError as exc:
        raise ExternalResponseMapperError(
            "BOND_DISCOVERY_EXTERNAL_API_FIELD_MAP must be valid JSON."
        ) from exc

    if not isinstance(mapping, dict):
        raise ExternalResponseMapperError(
            "BOND_DISCOVERY_EXTERNAL_API_FIELD_MAP must be a JSON object."
        )

    return mapping


def normalize_alias_list(value, fallback):
    """
    Normalize custom alias mapping.

    Args:
        value: String or list of strings.
        fallback: Fallback alias list.

    Returns:
        list[str]: Alias list.
    """
    if isinstance(value, str):
        cleaned_value = value.strip()

        return [cleaned_value] if cleaned_value else fallback

    if isinstance(value, list):
        aliases = [
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        ]

        return aliases or fallback

    return fallback


def resolve_field_value(item, aliases):
    """
    Resolve a value using multiple possible aliases.

    Supports:
        - normal keys: "isin"
        - dotted keys: "security.identifiers.isin"

    Args:
        item: Source object.
        aliases: List of possible aliases.

    Returns:
        Any: First non-empty value found, otherwise empty string.
    """
    for alias in aliases:
        value = get_value_by_path(
            item=item,
            path=alias,
        )

        if value is not None and value != "":
            return value

    return ""


def get_value_by_path(item, path):
    """
    Read a value from a dictionary using a simple dotted path.

    Args:
        item: Source dictionary.
        path: Field path.

    Returns:
        Any: Value or None.
    """
    if not path:
        return None

    current_value = item

    for part in path.split("."):
        if not isinstance(current_value, dict):
            return None

        current_value = current_value.get(part)

        if current_value is None:
            return None

    return current_value


def stringify_candidate_values(candidate):
    """
    Convert candidate values into safe string values.

    The discovery service will later parse decimals and dates properly.

    Args:
        candidate: Candidate dictionary.

    Returns:
        dict: Candidate dictionary with string values.
    """
    stringified_candidate = {}

    for field in CANONICAL_FIELDS:
        value = candidate.get(field, "")

        if value is None:
            value = ""

        stringified_candidate[field] = str(value).strip()

    return stringified_candidate