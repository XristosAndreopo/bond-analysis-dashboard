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

from bonds.ai_research.schemas import (
    BOND_MARKET_RESEARCH_RESULT_SCHEMA,
    DISCOVERY_RESEARCH_RESULT_SCHEMA,
)


DEFAULT_OPENAI_MODEL = "gpt-5.5"
DEFAULT_SEARCH_CONTEXT_SIZE = "medium"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_REASONING_EFFORT = "low"


class OpenAIResearchClientError(Exception):
    """
    Raised when the OpenAI research client cannot complete a request.
    """


def run_openai_discovery_research(
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """
    Run OpenAI Responses API web research for bond discovery.

    Args:
        system_prompt: System instructions for safe research behavior.
        user_prompt: Discovery task prompt.

    Returns:
        Parsed DiscoveryResearchResult dictionary.
    """
    return _run_openai_structured_research(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_definition=DISCOVERY_RESEARCH_RESULT_SCHEMA,
        request_label="OpenAI discovery research",
    )


def run_openai_market_research(
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """
    Run OpenAI Responses API web research for market data refresh.

    Args:
        system_prompt: System instructions for safe research behavior.
        user_prompt: Market refresh task prompt.

    Returns:
        Parsed BondMarketResearchResult dictionary.
    """
    return _run_openai_structured_research(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_definition=BOND_MARKET_RESEARCH_RESULT_SCHEMA,
        request_label="OpenAI market research",
    )


def _run_openai_structured_research(
    system_prompt: str,
    user_prompt: str,
    schema_definition: dict[str, Any],
    request_label: str,
) -> dict[str, Any]:
    """
    Run an OpenAI structured web-search request and parse the JSON result.

    Args:
        system_prompt: System instructions.
        user_prompt: User/task prompt.
        schema_definition: JSON schema definition from schemas.py.
        request_label: Human-readable label for error messages.

    Returns:
        Parsed JSON object.

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
    reasoning_effort = os.getenv(
        "OPENAI_REASONING_EFFORT",
        DEFAULT_REASONING_EFFORT,
    ).strip()
    max_output_tokens = _get_max_output_tokens()

    try:
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_prompt,
                        }
                    ],
                }
            ],
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": search_context_size,
                }
            ],
            tool_choice="auto",
            reasoning={
                "effort": reasoning_effort,
            },
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_definition["name"],
                    "strict": True,
                    "schema": schema_definition["schema"],
                }
            },
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:
        raise OpenAIResearchClientError(
            f"{request_label} request failed: {exc}"
        ) from exc

    output_text = _extract_response_output_text(response)

    if not output_text.strip():
        raise OpenAIResearchClientError(
            f"{request_label} returned an empty response."
        )

    parsed_payload = _parse_json_payload(output_text)

    if not isinstance(parsed_payload, dict):
        raise OpenAIResearchClientError(
            f"{request_label} response must be a JSON object."
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


def _extract_response_output_text(response: Any) -> str:
    """
    Extract text output from an OpenAI Responses API response.

    Args:
        response: OpenAI Responses API response object.

    Returns:
        Response text.
    """
    output_text = getattr(response, "output_text", "") or ""

    if output_text.strip():
        return output_text

    collected_text_parts: list[str] = []
    response_output = getattr(response, "output", None) or []

    for output_item in response_output:
        content_items = getattr(output_item, "content", None) or []

        for content_item in content_items:
            text = getattr(content_item, "text", None)

            if text:
                collected_text_parts.append(str(text))

    return "\n".join(collected_text_parts)


def _parse_json_payload(output_text: str) -> dict[str, Any]:
    """
    Parse a JSON payload from model output.

    The OpenAI request already asks for structured JSON. This parser adds
    resilience for cases where the output is wrapped in a Markdown code fence
    or contains extra text around the JSON object.

    Args:
        output_text: Raw response text.

    Returns:
        Parsed JSON object.

    Raises:
        OpenAIResearchClientError: If no valid JSON object can be parsed.
    """
    cleaned_text = _strip_markdown_code_fence(output_text)

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    extracted_json = _extract_first_json_object(cleaned_text)

    if extracted_json:
        try:
            return json.loads(extracted_json)
        except json.JSONDecodeError as exc:
            raise OpenAIResearchClientError(
                "OpenAI response contained a JSON-like object, but it could "
                f"not be parsed. Response preview: {_build_preview(output_text)}"
            ) from exc

    raise OpenAIResearchClientError(
        "OpenAI response was not valid JSON. "
        f"Response preview: {_build_preview(output_text)}"
    )


def _strip_markdown_code_fence(text: str) -> str:
    """
    Remove a Markdown JSON code fence if the response is wrapped in one.

    Args:
        text: Raw text.

    Returns:
        Text without surrounding Markdown code fence.
    """
    stripped_text = text.strip()

    if not stripped_text.startswith("```"):
        return stripped_text

    lines = stripped_text.splitlines()

    if len(lines) < 3:
        return stripped_text

    first_line = lines[0].strip().lower()
    last_line = lines[-1].strip()

    if first_line in {"```", "```json"} and last_line == "```":
        return "\n".join(lines[1:-1]).strip()

    return stripped_text


def _extract_first_json_object(text: str) -> str:
    """
    Extract the first balanced JSON object from text.

    Args:
        text: Raw text.

    Returns:
        JSON object text or empty string.
    """
    start_index = text.find("{")

    if start_index == -1:
        return ""

    brace_depth = 0
    in_string = False
    escape_next = False

    for index in range(start_index, len(text)):
        character = text[index]

        if escape_next:
            escape_next = False
            continue

        if character == "\\":
            escape_next = True
            continue

        if character == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if character == "{":
            brace_depth += 1
        elif character == "}":
            brace_depth -= 1

            if brace_depth == 0:
                return text[start_index : index + 1]

    return ""


def _build_preview(text: str, max_length: int = 600) -> str:
    """
    Build a compact response preview for error messages.

    Args:
        text: Raw response text.
        max_length: Maximum preview length.

    Returns:
        Compact preview string.
    """
    compact_text = " ".join(text.strip().split())

    if len(compact_text) <= max_length:
        return compact_text

    return f"{compact_text[:max_length]}..."
