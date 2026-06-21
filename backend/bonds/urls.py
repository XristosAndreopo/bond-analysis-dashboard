"""
URL routes for bond-related API endpoints.

This module registers:
- Bond master data endpoints
- Bond market data endpoints
- FX rate endpoints
- Bond discovery endpoints
- CSV bond universe upload endpoint

Discovery endpoints:
    GET  /api/discover-bonds/
    POST /api/discover-bonds/run/
    POST /api/discover-bonds/<id>/add-to-watchlist/
    POST /api/discover-bonds/<id>/ignore/
    POST /api/discover-bonds/upload-csv/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .discovery.upload_views import BondUniverseCSVUploadAPIView

from .views import (
    BondCandidateDiscoveryViewSet,
    BondMarketDataViewSet,
    BondViewSet,
    FXRateUpdateAPIView,
    FXRateViewSet,
)


router = DefaultRouter()
router.register("bonds", BondViewSet, basename="bonds")
router.register("market-data", BondMarketDataViewSet, basename="market-data")
router.register("fx-rates", FXRateViewSet, basename="fx-rates")
router.register(
    "discover-bonds",
    BondCandidateDiscoveryViewSet,
    basename="discover-bonds",
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
    path("", include(router.urls)),
]