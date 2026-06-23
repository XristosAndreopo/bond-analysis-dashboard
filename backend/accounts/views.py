"""
API views for user account data.

This module exposes:
- current authenticated user endpoint
- public signup endpoint
- public forgot password request placeholder

The forgot password endpoint currently returns a safe generic message. Real
email delivery and password reset token handling can be added in a later step.
"""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CurrentUserSerializer,
    ForgotPasswordRequestSerializer,
    SignupSerializer,
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

        Args:
            request: DRF request.

        Returns:
            Response: Serialized authenticated user.
        """
        serializer = CurrentUserSerializer(request.user)

        return Response(serializer.data)


class SignupAPIView(APIView):
    """
    Public endpoint for user registration.

    This endpoint creates a basic active user account using Django's built-in
    User model. It does not automatically issue JWT tokens; the frontend should
    redirect the user to login after successful signup.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Create a new user account.

        Args:
            request: DRF request containing signup fields.

        Returns:
            Response: Created user data without password fields.
        """
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "detail": "Account created successfully.",
                "user": CurrentUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
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
        Accept a forgot password request.

        Args:
            request: DRF request containing an email address.

        Returns:
            Response: Generic password reset message.
        """
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()

        # Placeholder for a future real password reset flow.
        #
        # We intentionally do not return different responses depending on
        # whether the email exists.
        _user_exists = User.objects.filter(email__iexact=email).exists()

        return Response(
            {
                "detail": (
                    "If an account exists for this email, password reset "
                    "instructions will be sent."
                )
            },
            status=status.HTTP_200_OK,
        )