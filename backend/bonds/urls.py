"""
URL configuration for the bonds app.

This file exposes:
- bond master data endpoints
- market data endpoints
- FX rate endpoints
- FX live update endpoint
- discovery endpoints
- CSV upload endpoint
- provider status endpoint
- OpenAI AI research discovery endpoint
- OpenAI Watchlist market refresh endpoint
- AI research JSON import endpoints
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .ai_research.views import (
    AIResearchDiscoveryImportAPIView,
    AIResearchDiscoveryRunAPIView,
    AIResearchMarketImportAPIView,
    AIResearchWatchlistMarketRefreshAPIView,
)
from .discovery.provider_status_views import DiscoveryProviderStatusAPIView
from .discovery.upload_views import BondUniverseCSVUploadAPIView
from .views import (
    BondCandidateDiscoveryViewSet,
    BondMarketDataViewSet,
    BondViewSet,
    FXRateUpdateAPIView,
    FXRateViewSet,
)


router = DefaultRouter()
router.register("bonds", BondViewSet, basename="bond")
router.register("market-data", BondMarketDataViewSet, basename="market-data")
router.register("fx-rates", FXRateViewSet, basename="fx-rate")
router.register(
    "discover-bonds",
    BondCandidateDiscoveryViewSet,
    basename="discover-bond",
)


urlpatterns = [
    path(
        "fx-rates/update/",
        FXRateUpdateAPIView.as_view(),
        name="fx-rate-update",
    ),
    path(
        "discover-bonds/upload-csv/",
        BondUniverseCSVUploadAPIView.as_view(),
        name="bond-universe-csv-upload",
    ),
    path(
        "discover-bonds/provider-status/",
        DiscoveryProviderStatusAPIView.as_view(),
        name="discovery-provider-status",
    ),
    path(
        "ai-research/discover/",
        AIResearchDiscoveryRunAPIView.as_view(),
        name="ai-research-discover",
    ),
    path(
        "ai-research/watchlist-market-refresh/",
        AIResearchWatchlistMarketRefreshAPIView.as_view(),
        name="ai-research-watchlist-market-refresh",
    ),
    path(
        "ai-research/import-discovery/",
        AIResearchDiscoveryImportAPIView.as_view(),
        name="ai-research-import-discovery",
    ),
    path(
        "ai-research/import-market/",
        AIResearchMarketImportAPIView.as_view(),
        name="ai-research-import-market",
    ),
    path("", include(router.urls)),
]
