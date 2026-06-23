"""
API views for Discover Bonds provider/workflow status.

This endpoint returns safe read-only diagnostics for the two supported
Discovery workflows:
- CSV Provider
- AI Research Provider
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bonds.discovery.providers.provider_health import get_provider_status_report


class DiscoveryProviderStatusAPIView(APIView):
    """
    Return provider/workflow status report for the authenticated user.

    Endpoint:
        GET /api/discover-bonds/provider-status/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return provider/workflow status report.
        """
        return Response(get_provider_status_report())
