"""
API views for user account data.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CurrentUserSerializer


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