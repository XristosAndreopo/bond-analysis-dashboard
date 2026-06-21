"""
API views for AI-researched bond data imports.

These endpoints do not call OpenAI yet.

They accept structured JSON that follows the AI Research schemas and import it
into the application database.

Important:
- AI-researched data is not treated as official live market feed data.
- Imported records keep source URL, retrieved timestamp, confidence,
  review status, missing fields, and raw research payload.
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bonds.ai_research.import_service import (
    AIResearchImportError,
    import_discovery_research_result,
    import_market_research_result,
)


class AIResearchDiscoveryImportAPIView(APIView):
    """
    Import AI-researched discovery results.

    Endpoint:
        POST /api/ai-research/import-discovery/

    Expected payload:
        DiscoveryResearchResult JSON.

    Result:
        Creates or updates BondCandidate records with:
        - data_origin = AI_RESEARCH
        - needs_review = true
        - review_status = NEEDS_REVIEW
        - source/source_url/retrieved_at/confidence metadata
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Import discovery research JSON for the authenticated user.
        """
        if not isinstance(request.data, dict):
            return Response(
                {"detail": "Request body must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import_summary = import_discovery_research_result(
                user=request.user,
                payload=request.data,
            )
        except AIResearchImportError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "AI discovery research imported successfully.",
                "import_summary": import_summary,
            },
            status=status.HTTP_200_OK,
        )


class AIResearchMarketImportAPIView(APIView):
    """
    Import AI-researched market refresh results.

    Endpoint:
        POST /api/ai-research/import-market/

    Expected payload:
        BondMarketResearchResult JSON.

    Result:
        Creates or updates BondMarketData records for bonds that already exist
        in the application.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Import market refresh research JSON.
        """
        if not isinstance(request.data, dict):
            return Response(
                {"detail": "Request body must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import_summary = import_market_research_result(
                payload=request.data,
            )
        except AIResearchImportError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "AI market research imported successfully.",
                "import_summary": import_summary,
            },
            status=status.HTTP_200_OK,
        )