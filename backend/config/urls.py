"""
Root URL configuration for the Bond Analysis Dashboard backend.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    # JWT authentication endpoints
    path(
        "api/auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Application API endpoints
    path(
        "api/accounts/",
        include("accounts.urls"),
    ),
    path(
        "api/",
        include("bonds.urls"),
    ),
    path(
        "api/",
        include("portfolios.urls"),
    ),
]