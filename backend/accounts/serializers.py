"""
Serializers for user account data.

This module contains serializers for:
- current authenticated user data
- public signup
- email verification
- resend verification code
- forgot password request
- password reset confirmation

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
            "is_active",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        """
        Return the user's full name if available; otherwise return username.
        """
        full_name = obj.get_full_name().strip()

        if full_name:
            return full_name

        return obj.username


class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer for public user registration.

    The user is created as inactive. The account becomes active only after
    successful email verification with a temporary code.
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
        Create a new inactive Django user.
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
        user.is_active = False
        user.save(update_fields=["is_active"])

        return user


class EmailCodeSerializer(serializers.Serializer):
    """
    Base serializer for forms that submit an email and a numeric code.
    """

    email = serializers.EmailField(required=True)
    code = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        trim_whitespace=True,
    )

    def validate_code(self, value):
        """
        Validate that code is exactly six numeric digits.
        """
        code = value.strip()

        if not code.isdigit():
            raise serializers.ValidationError("Code must contain only digits.")

        return code


class VerifyEmailSerializer(EmailCodeSerializer):
    """
    Serializer for email verification.
    """


class ResendVerificationCodeSerializer(serializers.Serializer):
    """
    Serializer for resending email verification codes.
    """

    email = serializers.EmailField(required=True)


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """
    Serializer for forgot password requests.
    """

    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(EmailCodeSerializer):
    """
    Serializer for password reset confirmation.
    """

    new_password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """
        Validate matching new passwords and password strength.
        """
        attrs = super().validate(attrs)

        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        validate_password(new_password)

        return attrs
