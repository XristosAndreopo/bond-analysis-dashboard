"""
API views for discovery provider status.

This endpoint allows the frontend to show a safe configuration/health summary
for the Bond Discovery providers without running discovery.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bonds.discovery.providers.provider_health import (
    get_provider_status_report,
)


class DiscoveryProviderStatusAPIView(APIView):
    """
    Return provider status report for the authenticated user.

    Endpoint:
        GET /api/discover-bonds/provider-status/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return provider status report.
        """
        return Response(get_provider_status_report())