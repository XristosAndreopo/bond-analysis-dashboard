"""
URL routes for account API endpoints.
"""

from django.urls import path

from .views import (
    CurrentUserAPIView,
    ForgotPasswordAPIView,
    SignupAPIView,
)


urlpatterns = [
    path(
        "me/",
        CurrentUserAPIView.as_view(),
        name="current-user",
    ),
    path(
        "signup/",
        SignupAPIView.as_view(),
        name="signup",
    ),
    path(
        "forgot-password/",
        ForgotPasswordAPIView.as_view(),
        name="forgot-password",
    ),
]