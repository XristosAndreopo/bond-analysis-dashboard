"""
URL routes for account API endpoints.
"""

from django.urls import path

from .views import CurrentUserAPIView


urlpatterns = [
    path(
        "me/",
        CurrentUserAPIView.as_view(),
        name="current-user",
    ),
]