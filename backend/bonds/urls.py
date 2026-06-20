"""
URL routes for bond-related API endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BondMarketDataViewSet,
    BondViewSet,
    FXRateUpdateAPIView,
    FXRateViewSet,
)

router = DefaultRouter()
router.register("bonds", BondViewSet, basename="bonds")
router.register("market-data", BondMarketDataViewSet, basename="market-data")
router.register("fx-rates", FXRateViewSet, basename="fx-rates")

urlpatterns = [
    path(
        "fx-rates/update/",
        FXRateUpdateAPIView.as_view(),
        name="fx-rate-update",
    ),
    path("", include(router.urls)),
]