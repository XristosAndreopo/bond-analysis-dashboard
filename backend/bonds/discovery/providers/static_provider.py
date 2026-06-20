"""
Static bond discovery provider.

This provider returns controlled sample bond candidates for MVP development.

Important:
    These records are NOT live market data.
    These records are NOT investment recommendations.
    These records are only used to test the discovery flow before integrating
    a CSV import provider or a real external market data provider.

Provider responsibility:
    - Return raw candidate dictionaries.
    - Do not filter by rating.
    - Do not filter by maturity.
    - Do not check user Watchlist or Portfolio.
    - Do not save anything to the database.

Filtering, validation, duplicate exclusion, and saving are handled by the
discovery service.
"""

from copy import deepcopy


SOURCE_NAME = "static_provider"
RATING_SOURCE = "Static MVP Sample"


STATIC_BOND_CANDIDATES = [
    {
        "isin": "XXDEMO000001",
        "name": "Demo United States Treasury Note 4.125% 2031",
        "issuer": "United States Treasury",
        "country": "US",
        "currency": "USD",
        "coupon_rate": "4.1250",
        "maturity_date": "2031-05-31",
        "credit_rating": "AA+",
        "rating_source": RATING_SOURCE,
        "market_price": "100.5000",
        "ytm": "4.10000",
        "duration": "4.450000",
        "source": SOURCE_NAME,
        "source_url": "",
        "notes": (
            "Sample investment-grade government bond candidate. "
            "Used only for MVP discovery testing."
        ),
    },
    {
        "isin": "XXDEMO000002",
        "name": "Demo Hellenic Republic Government Bond 3.875% 2028",
        "issuer": "Hellenic Republic",
        "country": "GR",
        "currency": "EUR",
        "coupon_rate": "3.8750",
        "maturity_date": "2028-06-15",
        "credit_rating": "BBB-",
        "rating_source": RATING_SOURCE,
        "market_price": "99.7500",
        "ytm": "3.95000",
        "duration": "2.100000",
        "source": SOURCE_NAME,
        "source_url": "",
        "notes": (
            "Sample minimum investment-grade government bond candidate. "
            "Used only for MVP discovery testing."
        ),
    },
    {
        "isin": "XXDEMO000003",
        "name": "Demo European Corporate Bond 4.500% 2030",
        "issuer": "Demo European Corporate Issuer",
        "country": "DE",
        "currency": "EUR",
        "coupon_rate": "4.5000",
        "maturity_date": "2030-09-20",
        "credit_rating": "A-",
        "rating_source": RATING_SOURCE,
        "market_price": "101.2000",
        "ytm": "4.25000",
        "duration": "3.700000",
        "source": SOURCE_NAME,
        "source_url": "",
        "notes": (
            "Sample investment-grade corporate bond candidate. "
            "Used only for MVP discovery testing."
        ),
    },
    {
        "isin": "XXDEMO000004",
        "name": "Demo High Yield Corporate Bond 6.750% 2029",
        "issuer": "Demo High Yield Issuer",
        "country": "US",
        "currency": "USD",
        "coupon_rate": "6.7500",
        "maturity_date": "2029-11-30",
        "credit_rating": "BB+",
        "rating_source": RATING_SOURCE,
        "market_price": "98.4000",
        "ytm": "7.10000",
        "duration": "3.250000",
        "source": SOURCE_NAME,
        "source_url": "",
        "notes": (
            "Sample below-investment-grade candidate. "
            "The discovery service should skip this candidate when the "
            "minimum rating is BBB-."
        ),
    },
    {
        "isin": "XXDEMO000005",
        "name": "Demo Matured Government Bond 2.000% 2020",
        "issuer": "Demo Matured Issuer",
        "country": "FR",
        "currency": "EUR",
        "coupon_rate": "2.0000",
        "maturity_date": "2020-01-15",
        "credit_rating": "A",
        "rating_source": RATING_SOURCE,
        "market_price": "100.0000",
        "ytm": "0.00000",
        "duration": "0.000000",
        "source": SOURCE_NAME,
        "source_url": "",
        "notes": (
            "Sample matured candidate. "
            "The discovery service should skip this candidate because its "
            "maturity date is in the past."
        ),
    },
]


def load_candidates():
    """
    Return raw static bond candidates.

    Returns:
        List of candidate dictionaries.

    Notes:
        A deep copy is returned so callers can safely normalize or modify
        dictionaries without mutating the provider-level sample data.
    """
    return deepcopy(STATIC_BOND_CANDIDATES)


def get_provider_name():
    """
    Return the provider name.

    Returns:
        Provider name string.
    """
    return SOURCE_NAME