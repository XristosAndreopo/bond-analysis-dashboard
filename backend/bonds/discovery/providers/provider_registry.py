"""
Provider registry for the Bond Discovery Engine.

This module centralizes supported discovery providers.

The discovery service should not import every provider directly. Instead, it
asks the registry for the requested provider. This keeps the discovery service
clean and makes it easier to add real external providers later.

Supported MVP providers:
- static_provider
- csv_provider
- external_json_provider
"""

from bonds.discovery.providers import (
    csv_provider,
    external_json_provider,
    static_provider,
)


DEFAULT_DISCOVERY_SOURCE = "static_provider"

SUPPORTED_PROVIDERS = {
    "static_provider": static_provider,
    "csv_provider": csv_provider,
    "external_json_provider": external_json_provider,
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
            f"Unsupported discovery source '{source}'. "
            f"Supported sources: {supported_sources}."
        )

    return provider


def get_supported_provider_names():
    """
    Return supported provider names.

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