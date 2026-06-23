"""
Backend services for OpenAI-backed AI bond research.

The service flow is:
1. Receive discovery or market-refresh inputs from the authenticated user.
2. Build a strict research prompt.
3. Call OpenAI Responses API with hosted web_search.
4. Parse structured JSON output.
5. Reuse the existing import service to validate and save database rows.

The import service remains the source of truth for database safety checks.
"""

from __future__ import annotations

from typing import Any

from bonds.ai_research.import_service import (
    AIResearchImportError,
    import_discovery_research_result,
    import_market_research_result,
)
from bonds.ai_research.openai_client import (
    OpenAIResearchClientError,
    run_openai_discovery_research,
    run_openai_market_research,
)
from bonds.ai_research.prompts import (
    AI_RESEARCH_SYSTEM_PROMPT,
    build_discovery_research_prompt,
    build_market_research_prompt,
)


class AIResearchServiceError(Exception):
    """
    Raised when the AI research workflow cannot be completed.
    """


def run_openai_discovery_and_import(
    user,
    filters: dict[str, Any],
) -> dict[str, Any]:
    """
    Run OpenAI-backed discovery and import valid candidates.

    Args:
        user: Authenticated Django user.
        filters: Validated discovery filters.

    Returns:
        Dictionary with the raw research payload and import summary.

    Raises:
        AIResearchServiceError: If OpenAI research or backend import fails.
    """
    prompt = build_discovery_research_prompt(filters)

    try:
        research_payload = run_openai_discovery_research(
            system_prompt=AI_RESEARCH_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
    except OpenAIResearchClientError as exc:
        raise AIResearchServiceError(str(exc)) from exc

    try:
        import_summary = import_discovery_research_result(
            user=user,
            payload=research_payload,
        )
    except AIResearchImportError as exc:
        raise AIResearchServiceError(str(exc)) from exc

    return {
        "research_payload": research_payload,
        "import_summary": import_summary,
    }


def run_openai_market_refresh_and_import(
    isins: list[str],
    base_currency: str | None = None,
) -> dict[str, Any]:
    """
    Run OpenAI-backed market refresh and import valid market data.

    Args:
        isins: ISINs that already exist in the application.
        base_currency: Optional selected base currency for context.

    Returns:
        Dictionary with the raw research payload and import summary.

    Raises:
        AIResearchServiceError: If OpenAI research or backend import fails.
    """
    normalized_isins = _normalize_isins(isins)

    if not normalized_isins:
        raise AIResearchServiceError("At least one ISIN is required.")

    prompt = build_market_research_prompt(
        isins=normalized_isins,
        base_currency=base_currency,
    )

    try:
        research_payload = run_openai_market_research(
            system_prompt=AI_RESEARCH_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
    except OpenAIResearchClientError as exc:
        raise AIResearchServiceError(str(exc)) from exc

    try:
        import_summary = import_market_research_result(
            payload=research_payload,
        )
    except AIResearchImportError as exc:
        raise AIResearchServiceError(str(exc)) from exc

    return {
        "research_payload": research_payload,
        "import_summary": import_summary,
    }


def _normalize_isins(isins: list[str]) -> list[str]:
    """
    Normalize and de-duplicate ISIN values.

    Args:
        isins: Raw ISIN list.

    Returns:
        Clean uppercase unique ISIN list.
    """
    normalized_isins: list[str] = []

    for isin in isins:
        normalized_isin = str(isin or "").strip().upper()

        if normalized_isin and normalized_isin not in normalized_isins:
            normalized_isins.append(normalized_isin)

    return normalized_isins
