
"""
API views for AI-researched bond data.

These endpoints support three workflows:

1. Backend OpenAI discovery
   The frontend sends filters to Django. Django calls OpenAI Responses API with
   hosted web search, validates structured JSON, imports valid candidates and
   returns the resulting Candidate Bonds.

2. Backend OpenAI Watchlist/Portfolio market refresh
   The frontend requests a refresh for the authenticated user's active
   Watchlist or Portfolio ISINs. Django calls OpenAI, imports valid
   BondMarketData rows, and the frontend reloads the relevant page.

3. Manual structured JSON import
   The frontend or a developer may still send already-produced structured JSON
   payloads to the import endpoints. This remains useful for testing and future
   workflows.

Important:
- AI-researched data is not treated as official live market feed data.
- Imported records keep source URL, retrieved timestamp, confidence,
  review status, missing fields, and raw research payload.
"""

from __future__ import annotations

from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bonds.ai_research.import_service import (
    AIResearchImportError,
    import_discovery_research_result,
    import_market_research_result,
)
from bonds.ai_research.services import (
    AIResearchServiceError,
    run_openai_discovery_and_import,
    run_openai_market_refresh_and_import,
)
from bonds.discovery.discovery_service import get_visible_candidates
from bonds.discovery.rating_utils import (
    INVESTMENT_GRADE_MIN_RATING,
    RatingError,
    normalize_rating,
)
from bonds.models import DiscoveryRun
from bonds.serializers import BondCandidateSerializer, DiscoveryRunSerializer
from portfolios.models import UserBond


class AIResearchDiscoveryRequestSerializer(serializers.Serializer):
    """
    Serializer for backend OpenAI discovery requests.

    Expected payload:
        {
            "min_rating": "BBB-",
            "currencies": ["EUR", "USD"],
            "countries": ["GR", "US"],
            "bond_types": ["GOVERNMENT", "CORPORATE"],
            "max_results": 6
        }

    Empty lists mean "all" for that filter group.
    """

    min_rating = serializers.CharField(
        required=False,
        default=INVESTMENT_GRADE_MIN_RATING,
    )
    currencies = serializers.ListField(
        child=serializers.CharField(max_length=3),
        required=False,
        allow_empty=True,
        default=list,
    )
    countries = serializers.ListField(
        child=serializers.CharField(max_length=2),
        required=False,
        allow_empty=True,
        default=list,
    )
    bond_types = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=False,
        allow_empty=True,
        default=list,
    )
    max_results = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        default=6,
    )

    def validate_min_rating(self, value):
        """
        Normalize and validate minimum credit rating.
        """
        try:
            return normalize_rating(value)
        except RatingError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_currencies(self, value):
        """
        Normalize currency filters.
        """
        normalized_currencies = []

        for currency in value:
            if not currency:
                continue

            normalized_currency = currency.upper().strip()

            if len(normalized_currency) != 3:
                raise serializers.ValidationError(
                    "Each currency must be a 3-letter code."
                )

            if normalized_currency not in normalized_currencies:
                normalized_currencies.append(normalized_currency)

        return normalized_currencies

    def validate_countries(self, value):
        """
        Normalize country filters.
        """
        normalized_countries = []

        for country in value:
            if not country:
                continue

            normalized_country = country.upper().strip()

            if len(normalized_country) != 2:
                raise serializers.ValidationError(
                    "Each country must be a 2-letter ISO-style code."
                )

            if normalized_country not in normalized_countries:
                normalized_countries.append(normalized_country)

        return normalized_countries

    def validate_bond_types(self, value):
        """
        Normalize bond type filters.
        """
        supported_bond_types = {
            "GOVERNMENT",
            "CORPORATE",
            "TREASURY",
            "MUNICIPAL",
            "OTHER",
        }
        normalized_bond_types = []

        for bond_type in value:
            if not bond_type:
                continue

            normalized_bond_type = bond_type.upper().strip()

            if normalized_bond_type not in supported_bond_types:
                supported_text = ", ".join(sorted(supported_bond_types))

                raise serializers.ValidationError(
                    f"Supported bond types: {supported_text}."
                )

            if normalized_bond_type not in normalized_bond_types:
                normalized_bond_types.append(normalized_bond_type)

        return normalized_bond_types


class AIResearchWatchlistMarketRefreshRequestSerializer(serializers.Serializer):
    """
    Serializer for refreshing active Watchlist market data.

    Expected payload:
        {
            "base_currency": "EUR",
            "max_items": 12
        }
    """

    base_currency = serializers.CharField(
        required=False,
        max_length=3,
        default="EUR",
    )
    max_items = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        default=12,
    )

    def validate_base_currency(self, value):
        """
        Normalize base currency.
        """
        normalized_currency = str(value or "EUR").strip().upper()

        if len(normalized_currency) != 3:
            raise serializers.ValidationError(
                "Base currency must be a 3-letter code."
            )

        return normalized_currency


class AIResearchDiscoveryRunAPIView(APIView):
    """
    Run OpenAI-backed bond discovery for the authenticated user.

    Endpoint:
        POST /api/ai-research/discover/

    Result:
        - Calls OpenAI from the backend.
        - Imports valid candidates through the existing import service.
        - Returns the current candidate list for the created DiscoveryRun.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Run OpenAI discovery and return imported candidates.
        """
        serializer = AIResearchDiscoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filters = {
            "countries": serializer.validated_data.get("countries", []),
            "currencies": serializer.validated_data.get("currencies", []),
            "minimum_rating": serializer.validated_data.get("min_rating"),
            "maturity_from": None,
            "maturity_to": None,
            "issuer_types": [],
            "bond_types": serializer.validated_data.get("bond_types", []),
            "max_results": serializer.validated_data.get("max_results", 6),
        }

        try:
            result = run_openai_discovery_and_import(
                user=request.user,
                filters=filters,
            )
        except AIResearchServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_summary = result["import_summary"]
        discovery_run = DiscoveryRun.objects.filter(
            id=import_summary.get("discovery_run_id"),
            user=request.user,
        ).first()

        visible_candidates = get_visible_candidates(user=request.user)

        if discovery_run is not None:
            visible_candidates = visible_candidates.filter(
                discovery_run=discovery_run,
            )

        return Response(
            {
                "detail": "OpenAI discovery research completed successfully.",
                "run": (
                    DiscoveryRunSerializer(discovery_run).data
                    if discovery_run is not None
                    else None
                ),
                "candidates": BondCandidateSerializer(
                    visible_candidates.select_related("user", "discovery_run"),
                    many=True,
                ).data,
                "import_summary": import_summary,
                "research_payload": result["research_payload"],
                "warnings": result["research_payload"].get("warnings", []),
            },
            status=status.HTTP_200_OK,
        )


class AIResearchWatchlistMarketRefreshAPIView(APIView):
    """
    Refresh market data for the authenticated user's active Watchlist bonds.

    Endpoint:
        POST /api/ai-research/watchlist-market-refresh/

    This endpoint does not create new Bond records. It only researches ISINs
    already present in the user's active Watchlist and imports BondMarketData
    rows for matching existing Bond master records.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Run OpenAI market refresh for active Watchlist ISINs.
        """
        serializer = AIResearchWatchlistMarketRefreshRequestSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        base_currency = serializer.validated_data["base_currency"]
        max_items = serializer.validated_data["max_items"]

        isins = list(
            UserBond.objects.filter(
                user=request.user,
                holding_type=UserBond.HoldingType.WATCHLIST,
                is_active=True,
            )
            .select_related("bond")
            .order_by("bond__isin")
            .values_list("bond__isin", flat=True)
            .distinct()[:max_items]
        )

        if not isins:
            return Response(
                {
                    "detail": "There are no active Watchlist bonds to refresh.",
                    "requested_isins": [],
                    "import_summary": {
                        "total_found": 0,
                        "total_created": 0,
                        "total_updated": 0,
                        "total_skipped": 0,
                        "errors": [],
                    },
                    "warnings": [],
                },
                status=status.HTTP_200_OK,
            )

        try:
            result = run_openai_market_refresh_and_import(
                isins=isins,
                base_currency=base_currency,
            )
        except AIResearchServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Watchlist market data refresh completed.",
                "requested_isins": isins,
                "import_summary": result["import_summary"],
                "research_payload": result["research_payload"],
                "warnings": result["research_payload"].get("warnings", []),
            },
            status=status.HTTP_200_OK,
        )


class AIResearchPortfolioMarketRefreshAPIView(APIView):
    """
    Refresh market data for the authenticated user's active Portfolio bonds.

    Endpoint:
        POST /api/ai-research/portfolio-market-refresh/

    This endpoint does not create new Bond records. It only researches ISINs
    already present in the user's active Portfolio and imports BondMarketData
    rows for matching existing Bond master records.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Run OpenAI market refresh for active Portfolio ISINs.
        """
        serializer = AIResearchWatchlistMarketRefreshRequestSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        base_currency = serializer.validated_data["base_currency"]
        max_items = serializer.validated_data["max_items"]

        isins = list(
            UserBond.objects.filter(
                user=request.user,
                holding_type=UserBond.HoldingType.PORTFOLIO,
                is_active=True,
            )
            .select_related("bond")
            .order_by("bond__isin")
            .values_list("bond__isin", flat=True)
            .distinct()[:max_items]
        )

        if not isins:
            return Response(
                {
                    "detail": "There are no active Portfolio bonds to refresh.",
                    "requested_isins": [],
                    "import_summary": {
                        "total_found": 0,
                        "total_created": 0,
                        "total_updated": 0,
                        "total_skipped": 0,
                        "errors": [],
                    },
                    "warnings": [],
                },
                status=status.HTTP_200_OK,
            )

        try:
            result = run_openai_market_refresh_and_import(
                isins=isins,
                base_currency=base_currency,
            )
        except AIResearchServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Portfolio market data refresh completed.",
                "requested_isins": isins,
                "import_summary": result["import_summary"],
                "research_payload": result["research_payload"],
                "warnings": result["research_payload"].get("warnings", []),
            },
            status=status.HTTP_200_OK,
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

