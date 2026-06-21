"""
Smoke test for AI Research JSON Import endpoints.

This script tests:
- POST /api/ai-research/import-discovery/

It uses DRF APIClient with force_authenticate, so you do not need to manually
copy JWT tokens for this backend test.

Important:
- This is a local smoke test only.
- It temporarily allows the Django test host "testserver" inside this script.
"""

from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


def utc_now_iso():
    """
    Return current UTC datetime in ISO format with Z suffix.
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")


User = get_user_model()
user = User.objects.filter(is_active=True).first()

if user is None:
    raise RuntimeError("No active user found. Create/login a user first.")

client = APIClient()
client.force_authenticate(user=user)

retrieved_at = utc_now_iso()

payload = {
    "research_type": "DISCOVERY",
    "query_summary": (
        "Smoke test AI discovery import for one test bond candidate."
    ),
    "filters": {
        "countries": ["US"],
        "currencies": ["USD"],
        "minimum_rating": "BBB-",
        "maturity_from": "2026-01-01",
        "maturity_to": "2035-12-31",
        "issuer_types": ["GOVERNMENT"],
        "bond_types": ["TREASURY"],
    },
    "retrieved_at": retrieved_at,
    "items": [
        {
            "isin": "USAI00000001",
            "name": "AI Research Test Bond 4.125% 2031",
            "issuer": "Test Issuer",
            "country": "US",
            "currency": "USD",
            "coupon_rate": "4.125",
            "maturity_date": "2031-05-31",
            "credit_rating": "AA+",
            "rating_source": "Test rating source",
            "bond_type": "TREASURY",
            "seniority": "SENIOR_UNSECURED",
            "coupon_frequency": 2,
            "market_price": "99.5000",
            "ytm": "4.25000",
            "duration": "4.800000",
            "primary_source_name": "AI Research Test Source",
            "primary_source_url": "https://example.com/test-bond-source",
            "sources": [
                {
                    "source_name": "AI Research Test Source",
                    "source_url": "https://example.com/test-bond-source",
                    "source_type": "OTHER",
                    "fields_supported": [
                        "isin",
                        "name",
                        "issuer",
                        "coupon_rate",
                        "maturity_date",
                        "credit_rating",
                        "market_price",
                        "ytm",
                        "duration",
                    ],
                    "notes": "Test-only source used for backend smoke testing.",
                }
            ],
            "retrieved_at": retrieved_at,
            "confidence": "MEDIUM",
            "needs_review": True,
            "review_status": "NEEDS_REVIEW",
            "research_notes": (
                "This is a test AI-researched candidate. "
                "It should not be treated as real market data."
            ),
            "missing_fields": [],
        }
    ],
    "warnings": [
        "This is a smoke test payload, not real financial research."
    ],
}

response = client.post(
    "/api/ai-research/import-discovery/",
    payload,
    format="json",
)

print("Status:", response.status_code)

try:
    print("Response:", response.json())
except ValueError:
    print("Raw response:", response.content.decode("utf-8", errors="replace"))