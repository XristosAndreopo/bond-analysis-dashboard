"""
URL routes for account API endpoints.
"""

from django.urls import path

from .views import (
    CurrentUserAPIView,
    ForgotPasswordAPIView,
    ResendVerificationCodeAPIView,
    ResetPasswordAPIView,
    SignupAPIView,
    VerifyEmailAPIView,
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
        "verify-email/",
        VerifyEmailAPIView.as_view(),
        name="verify-email",
    ),
    path(
        "resend-verification-code/",
        ResendVerificationCodeAPIView.as_view(),
        name="resend-verification-code",
    ),
    path(
        "forgot-password/",
        ForgotPasswordAPIView.as_view(),
        name="forgot-password",
    ),
    path(
        "reset-password/",
        ResetPasswordAPIView.as_view(),
        name="reset-password",
    ),
]
