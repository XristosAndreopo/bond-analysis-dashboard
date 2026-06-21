"""
Prompt builders for the AI bond research workflow.

The prompts in this module are intentionally strict because the application
will import the model response into structured database tables.

The AI Research Agent must:
- search the web only when requested by the backend workflow,
- return JSON only,
- include source URLs,
- avoid guessing missing financial values,
- mark uncertain data as LOW confidence and needs_review=True.
"""

from __future__ import annotations

from typing import Any


AI_RESEARCH_SYSTEM_PROMPT = """
You are an AI bond research assistant for a Django bond analysis dashboard.

Your job is to research publicly available bond information on the web and
return structured JSON only.

Critical rules:
1. Do not provide investment advice.
2. Do not invent ISINs, prices, yields, ratings, maturities, or issuers.
3. If a value cannot be verified from a source, return null for that value.
4. Every item must include at least one source URL.
5. Each source must explain which fields it supports.
6. Use ISO date format for dates: YYYY-MM-DD.
7. Use ISO datetime format for retrieval timestamps.
8. Coupon rates, YTM, required returns, and yields must be percentages,
   not ratios. Example: 4.125 means 4.125%.
9. Bond prices must be clean/market prices per 100 face value when available.
10. If the price or yield is delayed, indicative, or not clearly live,
    mention that in research_notes and set needs_review=true.
11. If different sources disagree, keep the most reliable source, explain the
    conflict in research_notes, and lower confidence.
12. Treat the result as AI-researched data, not official live market feed data.
13. Return JSON only. Do not include Markdown, explanations, or extra text.
""".strip()


def build_discovery_research_prompt(filters: dict[str, Any]) -> str:
    """
    Build the user prompt for AI bond discovery.

    Args:
        filters: Dictionary of discovery filters received from the app.

    Returns:
        A strict research prompt requesting JSON discovery output.
    """
    return f"""
Research active bonds that match the following filters.

Filters:
{_format_filters(filters)}

Goal:
Find bonds that can be imported as discovery candidates into a bond analysis
dashboard.

Return JSON using the DiscoveryResearchResult schema.

Required bond fields:
- isin
- name
- issuer
- country
- currency
- coupon_rate
- maturity_date
- credit_rating
- rating_source
- bond_type
- seniority
- coupon_frequency
- market_price
- ytm
- duration
- primary_source_name
- primary_source_url
- sources
- retrieved_at
- confidence
- needs_review
- review_status
- research_notes
- missing_fields

Rules:
- Include only bonds that appear to be active and not matured.
- If the requested minimum rating is provided, include only bonds that appear
  to satisfy it.
- If a field is not publicly available, set it to null and add the field name
  to missing_fields.
- Set review_status to NEEDS_REVIEW for all items.
- Set needs_review to true for all items unless every major field is verified
  from a reliable source.
- Use HIGH confidence only when the ISIN, issuer, coupon, maturity, and rating
  are clearly supported by reliable sources.
- Use MEDIUM confidence when core identity fields are supported but market data
  is indicative or incomplete.
- Use LOW confidence when the record needs significant manual checking.
- Return JSON only.
""".strip()


def build_market_research_prompt(
    isins: list[str],
    base_currency: str | None = None,
) -> str:
    """
    Build the user prompt for refreshing existing bond market data.

    Args:
        isins: List of ISINs already stored in the application.
        base_currency: Optional portfolio base currency.

    Returns:
        A strict research prompt requesting JSON market refresh output.
    """
    isin_lines = "\n".join(f"- {isin}" for isin in isins)
    base_currency_text = base_currency or "not specified"

    return f"""
Research the latest publicly available data for the following bond ISINs.

ISINs:
{isin_lines}

Portfolio base currency:
{base_currency_text}

Goal:
Refresh existing Watchlist/Portfolio bonds with AI-researched market data.

Return JSON using the BondMarketResearchResult schema.

Required fields for each ISIN:
- isin
- name
- issuer
- currency
- quote_date
- market_price
- ytm
- market_required_return
- bid_price
- ask_price
- credit_rating
- rating_source
- primary_source_name
- primary_source_url
- sources
- retrieved_at
- confidence
- needs_review
- review_status
- research_notes
- missing_fields

Rules:
- Do not invent market prices or yields.
- If a price is indicative, delayed, from a broker page, or unclear, keep it
  only if the source is visible and explain the limitation in research_notes.
- If YTM is not available, return null.
- If market_required_return is not available, return null.
- If bid or ask is unavailable, return null.
- Set review_status to NEEDS_REVIEW for all items.
- Set needs_review to true unless the item is strongly supported by reliable
  sources.
- Return JSON only.
""".strip()


def _format_filters(filters: dict[str, Any]) -> str:
    """
    Format discovery filters in a deterministic text block.

    Args:
        filters: Dictionary of discovery filters.

    Returns:
        Human-readable filter lines for the research prompt.
    """
    if not filters:
        return "- No filters provided."

    lines: list[str] = []

    for key in sorted(filters.keys()):
        value = filters[key]

        if isinstance(value, list):
            formatted_value = ", ".join(str(item) for item in value)
        elif value is None or value == "":
            formatted_value = "not specified"
        else:
            formatted_value = str(value)

        lines.append(f"- {key}: {formatted_value}")

    return "\n".join(lines)