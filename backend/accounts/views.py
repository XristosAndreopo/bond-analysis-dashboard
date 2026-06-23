"""
API views for user account data.

This module exposes:
- current authenticated user endpoint
- public signup endpoint with email verification code
- public email verification endpoint
- public verification-code resend endpoint
- public forgot password endpoint
- public reset password endpoint
"""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccountSecurityCode
from .serializers import (
    CurrentUserSerializer,
    ForgotPasswordRequestSerializer,
    ResendVerificationCodeSerializer,
    ResetPasswordSerializer,
    SignupSerializer,
    VerifyEmailSerializer,
)
from .services import (
    AccountSecurityCodeError,
    send_email_verification_code,
    send_password_reset_code,
    validate_security_code,
)


GENERIC_VERIFICATION_MESSAGE = (
    "If an inactive account exists for this email, a verification code will be sent."
)
GENERIC_PASSWORD_RESET_MESSAGE = (
    "If an active account exists for this email, password reset instructions will be sent."
)


class CurrentUserAPIView(APIView):
    """
    Return the currently authenticated user.

    The frontend uses this endpoint to display the username in the sidebar.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return current user data.
        """
        serializer = CurrentUserSerializer(request.user)

        return Response(serializer.data)


class SignupAPIView(APIView):
    """
    Public endpoint for user registration.

    This endpoint creates an inactive user and sends a temporary email
    verification code. The user can login only after successful verification.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Create a new inactive user account and send verification code.
        """
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        send_email_verification_code(user)

        return Response(
            {
                "detail": (
                    "Account created successfully. A verification code has "
                    "been sent to your email."
                ),
                "email": user.email,
                "user": CurrentUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    """
    Public endpoint for email verification.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Verify a user's email with a temporary numeric code.
        """
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = validate_security_code(
                email=serializer.validated_data["email"],
                plain_code=serializer.validated_data["code"],
                purpose=AccountSecurityCode.Purpose.EMAIL_VERIFICATION,
            )
        except AccountSecurityCodeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        return Response(
            {
                "detail": "Email verified successfully. You can now login.",
                "user": CurrentUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ResendVerificationCodeAPIView(APIView):
    """
    Public endpoint for resending email verification codes.

    The response is generic to avoid account enumeration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Resend a verification code to an inactive user.
        """
        serializer = ResendVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=False).first()

        if user is not None:
            send_email_verification_code(user)

        return Response(
            {"detail": GENERIC_VERIFICATION_MESSAGE},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordAPIView(APIView):
    """
    Public endpoint for forgot password requests.

    Security note:
        The response is always generic, even if the email does not exist. This
        prevents account enumeration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Send a password reset code when an active account exists.
        """
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user is not None:
            send_password_reset_code(user)

        return Response(
            {"detail": GENERIC_PASSWORD_RESET_MESSAGE},
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    """
    Public endpoint for confirming a password reset with a temporary code.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Reset a user's password after validating a temporary code.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = validate_security_code(
                email=serializer.validated_data["email"],
                plain_code=serializer.validated_data["code"],
                purpose=AccountSecurityCode.Purpose.PASSWORD_RESET,
            )
        except AccountSecurityCodeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password reset successfully. You can now login."},
            status=status.HTTP_200_OK,
        )
