"""
Prompt builders for the OpenAI-backed AI bond research workflow.

The prompts in this module are strict because the backend imports the model
response into structured database tables after validation.

Important rules:
- The application never treats AI-researched data as an official live market
  feed.
- The model must not invent missing financial values.
- The backend calculates YTM and duration when market price, coupon, maturity,
  face value and coupon frequency are available.
"""

from __future__ import annotations

from typing import Any


AI_RESEARCH_SYSTEM_PROMPT = """
You are an AI bond research assistant for a Django bond analysis dashboard.

Your task is to search the web for publicly available bond information and
return structured JSON only. The JSON will be validated and imported into a
backend database.

Critical rules:
1. Do not provide investment advice.
2. Do not recommend buying or selling securities.
3. Do not invent ISINs, prices, yields, ratings, maturities, issuers, coupons,
   countries, currencies, or source URLs.
4. If a value cannot be verified from a visible source, return null and add the
   field name to missing_fields.
5. Every item must include at least one source URL.
6. primary_source_url must be a real URL that supports the core identity or
   market data for the bond.
7. Use ISO date format for dates: YYYY-MM-DD.
8. Use ISO datetime format for retrieval timestamps.
9. Coupon rates, YTM, required returns, and yields must be percentages, not
   ratios. Example: 4.125 means 4.125%.
10. Bond prices must be clean/market prices per 100 face value when available.
11. If price/yield data is delayed, indicative, or not clearly live, explain it
    in research_notes and set needs_review=true.
12. If different sources disagree, keep the most reliable source, explain the
    conflict in research_notes, and lower confidence.
13. Prefer official issuer, exchange, regulator, or reputable financial data
    sources over generic snippets.
14. Treat the result as AI-researched data, not official live market feed data.
15. Return JSON only. Do not include Markdown, commentary, or extra text.
""".strip()


def build_discovery_research_prompt(filters: dict[str, Any]) -> str:
    """
    Build the user prompt for OpenAI-backed bond discovery.

    Args:
        filters: Discovery filters received from the frontend.

    Returns:
        Strict prompt requesting JSON discovery output.
    """
    max_results = filters.get("max_results") or 6

    return f"""
Research active bond candidates that match these filters.

Filters:
{_format_filters(filters)}

Goal:
Find up to {max_results} active bonds that can be imported as discovery
candidates into a bond analysis dashboard.

Focus on quality over quantity:
- Prefer fewer complete records over many incomplete records.
- Prefer active bonds that are not matured.
- Prefer records with verified ISIN, issuer, coupon, maturity, currency,
  credit rating, market price, and source URL.
- Include only bonds that appear to satisfy the requested minimum rating.
- If bond_types is empty, include all bond types.
- If countries is empty, include all countries.
- If currencies is empty, include all currencies.

Return JSON using the DiscoveryResearchResult schema.

Required item fields:
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

Backend calculation rule:
- If YTM is unavailable, return ytm as null. The backend may calculate it.
- If duration is unavailable, return duration as null. The backend may calculate it.
- Do not guess YTM or duration.
- However, market_price, coupon_rate, maturity_date, currency, ISIN, issuer,
  credit_rating and source URL should be verified whenever possible, otherwise
  the backend may skip the candidate.

Source rules:
- sources must contain at least one source object.
- fields_supported must identify which fields the source supports.
- primary_source_url must not be empty.

Review rules:
- Set review_status to NEEDS_REVIEW for all items.
- Set needs_review to true unless every major field is strongly verified.
- Use HIGH confidence only when ISIN, issuer, coupon, maturity, rating and
  market price are clearly supported by reliable sources.
- Use MEDIUM confidence when identity fields are supported but market data is
  indicative, delayed or incomplete.
- Use LOW confidence when significant manual checking is needed.

Return JSON only.
""".strip()


def build_market_research_prompt(
    isins: list[str],
    base_currency: str | None = None,
) -> str:
    """
    Build the user prompt for refreshing existing bond market data.

    Args:
        isins: ISINs already stored in the application.
        base_currency: Optional portfolio base currency.

    Returns:
        Strict prompt requesting JSON market refresh output.
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
        filters: Discovery filter dictionary.

    Returns:
        Human-readable filter lines for the research prompt.
    """
    if not filters:
        return "- No filters provided."

    lines: list[str] = []

    for key in sorted(filters.keys()):
        value = filters[key]

        if isinstance(value, list):
            formatted_value = ", ".join(str(item) for item in value) or "all"
        elif value is None or value == "":
            formatted_value = "not specified"
        else:
            formatted_value = str(value)

        lines.append(f"- {key}: {formatted_value}")

    return "\n".join(lines)
