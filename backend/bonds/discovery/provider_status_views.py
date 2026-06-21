"""
API views for discovery provider status and external provider testing.

These endpoints allow the frontend to show safe read-only diagnostics for the
Bond Discovery providers.

They do not create:
- BondCandidate records
- Bond records
- Portfolio records
- Watchlist records
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bonds.discovery.providers.external_provider_test import (
    run_external_provider_test,
)
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


class DiscoveryExternalProviderTestAPIView(APIView):
    """
    Test the external JSON/API provider safely.

    Endpoint:
        GET /api/discover-bonds/test-external-provider/

    This endpoint loads and validates external provider data but does not save
    anything to the database.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return external provider test result.
        """
        return Response(run_external_provider_test())