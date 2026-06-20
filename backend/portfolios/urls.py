"""
URL routes for Dashboard, Portfolio, Watchlist, and UserBond detail APIs.
"""

from django.urls import path

from .views import (
    DashboardAPIView,
    MoveUserBondAPIView,
    PortfolioAPIView,
    UserBondDetailAPIView,
    WatchlistAPIView,
)


urlpatterns = [
    path(
        "dashboard/",
        DashboardAPIView.as_view(),
        name="dashboard",
    ),
    path(
        "portfolio/",
        PortfolioAPIView.as_view(),
        name="portfolio",
    ),
    path(
        "watchlist/",
        WatchlistAPIView.as_view(),
        name="watchlist",
    ),
    path(
        "positions/<int:pk>/",
        UserBondDetailAPIView.as_view(),
        name="user-bond-detail",
    ),
    path(
        "positions/<int:pk>/move/",
        MoveUserBondAPIView.as_view(),
        name="move-user-bond",
    ),
]