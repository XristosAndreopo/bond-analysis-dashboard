"""
Serializers for user account data.
"""

from django.contrib.auth.models import User
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
        """
        full_name = obj.get_full_name().strip()

        if full_name:
            return full_name

        return obj.username