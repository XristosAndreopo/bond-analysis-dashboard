"""
URL routes for bond-related API endpoints.

This module registers:
- Bond master data endpoints
- Bond market data endpoints
- FX rate endpoints
- Bond discovery endpoints

Discovery endpoints:
    GET  /api/discover-bonds/
    POST /api/discover-bonds/run/
    POST /api/discover-bonds/<id>/add-to-watchlist/
    POST /api/discover-bonds/<id>/ignore/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

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
    path("", include(router.urls)),
]