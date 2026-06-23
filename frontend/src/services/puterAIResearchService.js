/**
 * Puter AI Research Service.
 *
 * This service uses Puter.js from the frontend to generate structured
 * AI-researched bond discovery JSON.
 *
 * Important:
 * - This does not use the backend OpenAI API.
 * - This does not require an OpenAI API key in Django.
 * - The generated JSON is not saved directly.
 * - The frontend must send the generated JSON to the Django import endpoint.
 * - The backend remains responsible for validation and database import.
 *
 * Data policy:
 * - AI-researched data is not official live market feed data.
 * - Every item must include source URL, retrieved_at, confidence,
 *   needs_review and review_status.
 */

import { puter } from "@heyputer/puter.js";

const DEFAULT_PUTER_MODEL =
  import.meta.env.VITE_PUTER_AI_MODEL || "openai/gpt-5.2-chat";

const DEFAULT_MAX_TOKENS = 6000;
const DEFAULT_TEMPERATURE = 0.1;

/**
 * Generate DiscoveryResearchResult JSON using Puter AI with web search.
 *
 * @param {object} filters - Discovery filters from the frontend.
 * @returns {Promise<object>} Parsed DiscoveryResearchResult JSON.
 */
export async function generateDiscoveryResearchJson(filters = {}) {
  const prompt = buildDiscoveryResearchPrompt(filters);

  const response = await puter.ai.chat(prompt, {
    model: DEFAULT_PUTER_MODEL,
    temperature: DEFAULT_TEMPERATURE,
    max_tokens: DEFAULT_MAX_TOKENS,
    tools: [{ type: "web_search" }],
  });

  const responseText = extractTextFromPuterResponse(response);
  const jsonText = extractJsonObjectText(responseText);

  return JSON.parse(jsonText);
}

/**
 * Build the strict AI research prompt.
 *
 * @param {object} filters - User-selected filters.
 * @returns {string} Prompt text.
 */
function buildDiscoveryResearchPrompt(filters) {
  const nowIso = new Date().toISOString();

  return `
You are an AI bond research assistant for a Django bond analysis dashboard.

Your task:
Search the web and return structured JSON only.

Important:
- Do not provide investment advice.
- Do not invent ISINs, prices, yields, ratings, maturities, or issuers.
- If a value cannot be verified from a source, return null.
- Every item must include at least one source URL.
- Every source must explain which fields it supports.
- Coupon rates, YTM, and yields must be percentages, not ratios.
  Example: 4.125 means 4.125%.
- Bond prices must be clean/market prices per 100 face value when available.
- If market price or yield is delayed, indicative, or not clearly live, explain
  that in research_notes and set needs_review to true.
- Set review_status to "NEEDS_REVIEW" for every item.
- Return JSON only. Do not include Markdown or explanation outside JSON.

User filters:
${formatFilters(filters)}

Current retrieval timestamp:
${nowIso}

Return exactly this JSON structure:

{
  "research_type": "DISCOVERY",
  "query_summary": "string",
  "filters": {
    "countries": ["string"],
    "currencies": ["string"],
    "minimum_rating": "string or null",
    "maturity_from": "YYYY-MM-DD or null",
    "maturity_to": "YYYY-MM-DD or null",
    "issuer_types": ["string"],
    "bond_types": ["string"]
  },
  "retrieved_at": "${nowIso}",
  "items": [
    {
      "isin": "string",
      "name": "string",
      "issuer": "string",
      "country": "2-letter country code if possible",
      "currency": "3-letter currency code",
      "coupon_rate": "number as string or null",
      "maturity_date": "YYYY-MM-DD or null",
      "credit_rating": "string or null",
      "rating_source": "string or null",
      "bond_type": "string or null",
      "seniority": "string or null",
      "coupon_frequency": 1,
      "market_price": "number as string or null",
      "ytm": "number as string or null",
      "duration": "number as string or null",
      "primary_source_name": "string",
      "primary_source_url": "string",
      "sources": [
        {
          "source_name": "string",
          "source_url": "string",
          "source_type": "OFFICIAL_ISSUER or EXCHANGE or REGULATOR or BROKER or DATA_VENDOR or NEWS or OTHER",
          "fields_supported": ["isin", "name"],
          "notes": "string"
        }
      ],
      "retrieved_at": "${nowIso}",
      "confidence": "HIGH or MEDIUM or LOW",
      "needs_review": true,
      "review_status": "NEEDS_REVIEW",
      "research_notes": "string",
      "missing_fields": ["string"]
    }
  ],
  "warnings": ["string"]
}

Search goal:
Find active bonds that match the filters. Prefer official issuer, exchange,
regulator, broker, or recognized data-vendor pages. If market price, YTM,
duration or rating cannot be verified, return null and add the field name to
missing_fields.

Return JSON only.
`.trim();
}

/**
 * Format user filters for the prompt.
 *
 * @param {object} filters - Filters object.
 * @returns {string} Text block.
 */
function formatFilters(filters) {
  if (!filters || Object.keys(filters).length === 0) {
    return "- No filters provided.";
  }

  return Object.keys(filters)
    .sort()
    .map((key) => {
      const value = filters[key];

      if (Array.isArray(value)) {
        return `- ${key}: ${value.length > 0 ? value.join(", ") : "not specified"}`;
      }

      if (value === null || value === undefined || value === "") {
        return `- ${key}: not specified`;
      }

      return `- ${key}: ${value}`;
    })
    .join("\n");
}

/**
 * Extract response text from possible Puter response shapes.
 *
 * Puter may return either a string-like response or an object depending on
 * model/provider behavior. This helper keeps parsing defensive.
 *
 * @param {unknown} response - Puter response.
 * @returns {string} Response text.
 */
function extractTextFromPuterResponse(response) {
  if (typeof response === "string") {
    return response;
  }

  if (response === null || response === undefined) {
    throw new Error("Puter AI returned an empty response.");
  }

  if (typeof response === "object") {
    if (typeof response.text === "string") {
      return response.text;
    }

    if (typeof response.message?.content === "string") {
      return response.message.content;
    }

    if (Array.isArray(response.message?.content)) {
      return response.message.content
        .map((part) => part?.text || "")
        .join("")
        .trim();
    }

    if (typeof response.content === "string") {
      return response.content;
    }

    if (typeof response.toString === "function") {
      const text = response.toString();

      if (text && text !== "[object Object]") {
        return text;
      }
    }
  }

  throw new Error("Could not extract text from Puter AI response.");
}

/**
 * Extract the first JSON object from text.
 *
 * This is defensive because some models may accidentally wrap JSON in text.
 *
 * @param {string} text - Raw response text.
 * @returns {string} JSON object text.
 */
function extractJsonObjectText(text) {
  const cleanedText = String(text || "")
    .trim()
    .replace(/^```json/i, "")
    .replace(/^```/i, "")
    .replace(/```$/i, "")
    .trim();

  const firstBraceIndex = cleanedText.indexOf("{");
  const lastBraceIndex = cleanedText.lastIndexOf("}");

  if (firstBraceIndex === -1 || lastBraceIndex === -1) {
    throw new Error("AI response did not contain a JSON object.");
  }

  return cleanedText.slice(firstBraceIndex, lastBraceIndex + 1);
}