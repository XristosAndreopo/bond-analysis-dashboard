"""
OpenAI client wrapper for AI bond research.

This module is intentionally small and isolated so the rest of the Django app
is not coupled directly to the OpenAI SDK.

The SDK import is lazy. This allows `python manage.py check` to keep working
before the developer installs the optional OpenAI dependency. The first real
AI request will return a clear error if the dependency or API key is missing.
"""

from __future__ import annotations

import json
import os
from typing import Any

from bonds.ai_research.schemas import DISCOVERY_RESEARCH_RESULT_SCHEMA


DEFAULT_OPENAI_MODEL = "gpt-5.5"
DEFAULT_SEARCH_CONTEXT_SIZE = "medium"
DEFAULT_MAX_OUTPUT_TOKENS = 12000


class OpenAIResearchClientError(Exception):
    """
    Raised when the OpenAI research client cannot complete a request.
    """


def run_openai_discovery_research(
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """
    Run OpenAI Responses API web research and return parsed JSON.

    Args:
        system_prompt: System instructions for safe research behavior.
        user_prompt: Discovery task prompt.

    Returns:
        Parsed DiscoveryResearchResult dictionary.

    Raises:
        OpenAIResearchClientError: If configuration, API call, or JSON parsing
        fails.
    """
    client = _build_openai_client()
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
    search_context_size = os.getenv(
        "OPENAI_WEB_SEARCH_CONTEXT_SIZE",
        DEFAULT_SEARCH_CONTEXT_SIZE,
    ).strip()
    max_output_tokens = _get_max_output_tokens()

    try:
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=user_prompt,
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": search_context_size,
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": DISCOVERY_RESEARCH_RESULT_SCHEMA["name"],
                    "strict": True,
                    "schema": DISCOVERY_RESEARCH_RESULT_SCHEMA["schema"],
                }
            },
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:
        raise OpenAIResearchClientError(
            f"OpenAI discovery research request failed: {exc}"
        ) from exc

    output_text = getattr(response, "output_text", "") or ""

    if not output_text.strip():
        raise OpenAIResearchClientError(
            "OpenAI returned an empty discovery research response."
        )

    try:
        parsed_payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise OpenAIResearchClientError(
            "OpenAI response was not valid JSON."
        ) from exc

    if not isinstance(parsed_payload, dict):
        raise OpenAIResearchClientError(
            "OpenAI response must be a JSON object."
        )

    return parsed_payload


def _build_openai_client():
    """
    Build the official OpenAI Python SDK client.

    Returns:
        OpenAI client instance.

    Raises:
        OpenAIResearchClientError: If the SDK or API key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise OpenAIResearchClientError(
            "OPENAI_API_KEY is missing. Add it to backend/.env before using "
            "AI Research Provider."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAIResearchClientError(
            "The OpenAI Python package is not installed. Run: pip install openai"
        ) from exc

    return OpenAI(api_key=api_key)


def _get_max_output_tokens() -> int:
    """
    Read max output tokens from the environment safely.

    Returns:
        Positive integer token limit.
    """
    raw_value = os.getenv(
        "OPENAI_MAX_OUTPUT_TOKENS",
        str(DEFAULT_MAX_OUTPUT_TOKENS),
    ).strip()

    try:
        parsed_value = int(raw_value)
    except ValueError:
        return DEFAULT_MAX_OUTPUT_TOKENS

    if parsed_value <= 0:
        return DEFAULT_MAX_OUTPUT_TOKENS

    return parsed_value
