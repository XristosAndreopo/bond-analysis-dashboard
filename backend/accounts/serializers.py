"""
Serializers for user account data.

This module contains serializers for:
- current authenticated user data
- public signup
- forgot password request placeholder

The application currently uses Django's built-in User model.
"""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the currently authenticated user.

    This is used by the frontend to display the username in the sidebar.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        """
        Return the user's full name if available; otherwise return username.

        Args:
            obj: Django User instance.

        Returns:
            str: Full name or username.
        """
        full_name = obj.get_full_name().strip()

        if full_name:
            return full_name

        return obj.username


class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer for public user registration.

    The serializer validates:
    - unique username
    - unique email when email is provided
    - password confirmation
    - Django password strength rules
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "username": {"required": True},
            "email": {"required": True},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate_username(self, value):
        """
        Validate that username is unique case-insensitively.

        Args:
            value: Submitted username.

        Returns:
            str: Cleaned username.

        Raises:
            serializers.ValidationError: If username already exists.
        """
        username = value.strip()

        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )

        return username

    def validate_email(self, value):
        """
        Validate that email is unique case-insensitively.

        Args:
            value: Submitted email.

        Returns:
            str: Normalized email.

        Raises:
            serializers.ValidationError: If email already exists.
        """
        email = value.strip().lower()

        if not email:
            raise serializers.ValidationError("Email is required.")

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def validate(self, attrs):
        """
        Validate matching passwords and password strength.

        Args:
            attrs: Submitted serializer data.

        Returns:
            dict: Validated data.

        Raises:
            serializers.ValidationError: If passwords do not match or are weak.
        """
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        validate_password(password)

        return attrs

    def create(self, validated_data):
        """
        Create a new active Django user.

        Args:
            validated_data: Validated signup data.

        Returns:
            User: Created user instance.
        """
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        return user


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """
    Serializer for forgot password requests.

    This MVP serializer only accepts an email address. The API response remains
    intentionally generic so the backend does not reveal whether an account
    exists for the submitted email.
    """

    email = serializers.EmailField(required=True)