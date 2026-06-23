"""
Provider registry for the Bond Discovery Engine.

This module centralizes backend discovery providers.

Current data strategy:
- CSV Provider is the only backend provider that run_bond_discovery() executes.
- AI Research is handled by the backend OpenAI workflow, not by this registry.
  The frontend calls /api/ai-research/discover/ and the backend performs
  OpenAI web research, structured JSON validation, and candidate import.

Static sample discovery has been removed so Discover Bonds focuses on real
user-provided CSV data and AI-researched candidates.
"""

from bonds.discovery.providers import csv_provider


DEFAULT_DISCOVERY_SOURCE = "csv_provider"

SUPPORTED_PROVIDERS = {
    "csv_provider": csv_provider,
}


class ProviderRegistryError(Exception):
    """
    Raised when a requested discovery provider is not supported.
    """


def normalize_provider_name(source):
    """
    Normalize provider source name.

    Args:
        source: Raw provider name.

    Returns:
        str: Normalized provider name.
    """
    if source is None:
        return DEFAULT_DISCOVERY_SOURCE

    normalized_source = str(source).strip().lower()

    if not normalized_source:
        return DEFAULT_DISCOVERY_SOURCE

    return normalized_source


def get_provider(source=None):
    """
    Return the provider module for a source name.

    Args:
        source: Provider source name.

    Returns:
        Provider module.

    Raises:
        ProviderRegistryError: If provider is unsupported.
    """
    normalized_source = normalize_provider_name(source)
    provider = SUPPORTED_PROVIDERS.get(normalized_source)

    if provider is None:
        supported_sources = ", ".join(get_supported_provider_names())

        raise ProviderRegistryError(
            f"Unsupported backend discovery source '{source}'. "
            f"Supported backend sources: {supported_sources}."
        )

    return provider


def get_supported_provider_names():
    """
    Return supported backend provider names.

    Returns:
        list[str]: Sorted supported provider names.
    """
    return sorted(SUPPORTED_PROVIDERS.keys())


def is_supported_provider(source):
    """
    Check whether a provider source is supported.

    Args:
        source: Provider source name.

    Returns:
        bool: True if supported.
    """
    normalized_source = normalize_provider_name(source)

    return normalized_source in SUPPORTED_PROVIDERS
