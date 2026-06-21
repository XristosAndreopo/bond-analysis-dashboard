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
- external provider test endpoint
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .discovery.provider_status_views import (
    DiscoveryExternalProviderTestAPIView,
    DiscoveryProviderStatusAPIView,
)
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
        "discover-bonds/test-external-provider/",
        DiscoveryExternalProviderTestAPIView.as_view(),
        name="discovery-external-provider-test",
    ),
    path("", include(router.urls)),
]