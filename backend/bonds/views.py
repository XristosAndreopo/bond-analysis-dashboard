"""
API views for bonds, market data, FX rates, live FX updates, and discovery.

This module exposes API endpoints for:
- bond master data
- bond market data
- manual FX rates
- live FX rate update action
- discovered bond candidates

Market data and FX rates use an upsert-style behavior. If a record already
exists for the same unique fields, it is updated instead of returning a
duplicate unique constraint error.

Discovery endpoints are user-specific:
- users see only their own candidates
- candidates already active in Portfolio or Watchlist are excluded
- optional discovery_run_id filtering keeps the UI focused on one run
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from bonds.discovery.discovery_service import (
    DiscoveryServiceError,
    add_candidate_to_watchlist,
    get_visible_candidates,
    ignore_candidate,
    run_bond_discovery,
)
from bonds.fx_services import FXRateUpdateError, update_latest_fx_rates

from .models import Bond, BondCandidate, BondMarketData, FXRate
from .serializers import (
    BondCandidateSerializer,
    BondMarketDataSerializer,
    BondSerializer,
    DiscoveryRunSerializer,
    FXRateSerializer,
    FXRateUpdateRequestSerializer,
    RunBondDiscoverySerializer,
)


class BondViewSet(ModelViewSet):
    """
    API endpoint for bond master data.

    Authenticated users can create and read bond records. Bonds are shared
    master data, while Portfolio and Watchlist ownership remains user-specific.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BondSerializer

    def get_queryset(self):
        """
        Return bonds filtered by optional search query.

        Query parameters:
            search: Optional text search against ISIN, name, or issuer.
        """
        queryset = Bond.objects.all().order_by("isin")
        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(isin__icontains=search)
                | Q(name__icontains=search)
                | Q(issuer__icontains=search)
            )

        return queryset


class BondMarketDataViewSet(ModelViewSet):
    """
    API endpoint for bond market data.

    Saving market data automatically triggers recalculation of related analyses
    through Django signals.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BondMarketDataSerializer

    def get_queryset(self):
        """
        Return market data filtered by optional bond id.

        Query parameters:
            bond: Optional bond id.
        """
        queryset = BondMarketData.objects.select_related(
            "bond",
        ).order_by(
            "-quote_date",
            "-created_at",
        )

        bond_id = self.request.query_params.get("bond")

        if bond_id:
            queryset = queryset.filter(bond_id=bond_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create or update market data.

        If a record already exists for the same:
        - bond
        - quote_date
        - source

        then the existing record is updated.
        """
        bond_id = request.data.get("bond")
        quote_date = request.data.get("quote_date")
        source = request.data.get("source") or "manual"

        existing_market_data = None

        if bond_id and quote_date and source:
            existing_market_data = BondMarketData.objects.filter(
                bond_id=bond_id,
                quote_date=quote_date,
                source=source,
            ).first()

        if existing_market_data is not None:
            serializer = self.get_serializer(
                existing_market_data,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class FXRateViewSet(ModelViewSet):
    """
    API endpoint for manual FX rates.

    Example:
        base_currency: USD
        quote_currency: EUR
        rate: 0.92000000

    Meaning:
        1 USD = 0.92 EUR
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FXRateSerializer

    def get_queryset(self):
        """
        Return FX rates filtered by optional currencies.

        Query parameters:
            base_currency: Optional source currency.
            quote_currency: Optional target currency.
        """
        queryset = FXRate.objects.all().order_by(
            "-rate_date",
            "base_currency",
            "quote_currency",
        )

        base_currency = self.request.query_params.get("base_currency")
        quote_currency = self.request.query_params.get("quote_currency")

        if base_currency:
            queryset = queryset.filter(base_currency=base_currency.upper())

        if quote_currency:
            queryset = queryset.filter(quote_currency=quote_currency.upper())

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create or update FX rate.

        If a record already exists for the same:
        - base_currency
        - quote_currency
        - rate_date
        - source

        then the existing record is updated.
        """
        base_currency = (request.data.get("base_currency") or "").upper()
        quote_currency = (request.data.get("quote_currency") or "").upper()
        rate_date = request.data.get("rate_date")
        source = request.data.get("source") or "manual"

        existing_fx_rate = None

        if base_currency and quote_currency and rate_date and source:
            existing_fx_rate = FXRate.objects.filter(
                base_currency=base_currency,
                quote_currency=quote_currency,
                rate_date=rate_date,
                source=source,
            ).first()

        if existing_fx_rate is not None:
            serializer = self.get_serializer(
                existing_fx_rate,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class FXRateUpdateAPIView(APIView):
    """
    API endpoint for updating live FX rates.

    This endpoint allows the frontend to trigger FX updates without using the
    terminal management command.

    Expected payload:
        {
            "quote_currency": "EUR",
            "base_currencies": ["USD", "GBP", "CHF", "JPY"]
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Fetch and save latest FX rates.
        """
        serializer = FXRateUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quote_currency = serializer.validated_data.get(
            "quote_currency",
            "EUR",
        )
        base_currencies = serializer.validated_data.get(
            "base_currencies",
            None,
        )

        try:
            result = update_latest_fx_rates(
                quote_currency=quote_currency,
                base_currencies=base_currencies,
            )
        except FXRateUpdateError as exc:
            return Response(
                {
                    "updated": [],
                    "errors": [str(exc)],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_rows = [
            {
                "base_currency": item.base_currency,
                "quote_currency": item.quote_currency,
                "rate_date": item.rate_date,
                "rate": str(item.rate),
                "created": item.created,
            }
            for item in result["updated"]
        ]

        return Response(
            {
                "updated": updated_rows,
                "errors": result["errors"],
            },
            status=status.HTTP_200_OK,
        )


class BondCandidateDiscoveryViewSet(ListModelMixin, GenericViewSet):
    """
    API endpoint for discovered bond candidates.

    Main endpoints:
        GET  /api/discover-bonds/
        POST /api/discover-bonds/run/
        POST /api/discover-bonds/clear-current/
        POST /api/discover-bonds/<id>/add-to-watchlist/
        POST /api/discover-bonds/<id>/ignore/

    Optional GET query parameters:
        discovery_run_id:
            If provided, only visible candidates from this specific run are
            returned. This prevents the frontend from mixing candidates from
            older discovery runs with the latest filtered run.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BondCandidateSerializer

    def get_queryset(self):
        """
        Return visible discovered bond candidates for the authenticated user.

        Query parameters:
            discovery_run_id:
                Optional DiscoveryRun id. If provided, only candidates from
                that run are returned.

        Visible candidates are:
        - owned by the logged-in user
        - status NEW or REVIEWED
        - not already active in Portfolio
        - not already active in Watchlist
        """
        queryset = get_visible_candidates(
            user=self.request.user,
        ).select_related(
            "user",
            "discovery_run",
        )

        discovery_run_id = self.request.query_params.get("discovery_run_id")

        if discovery_run_id:
            if not discovery_run_id.isdigit():
                return queryset.none()

            queryset = queryset.filter(
                discovery_run_id=discovery_run_id,
                discovery_run__user=self.request.user,
            )

        return queryset

    @action(detail=False, methods=["post"], url_path="run")
    def run(self, request):
        """
        Run bond discovery for the authenticated user.

        Request payload example:
            {
                "source": "csv_provider",
                "min_rating": "BBB-",
                "currencies": ["EUR", "USD"],
                "countries": ["GR", "US"],
                "bond_types": ["GOVERNMENT", "CORPORATE"]
            }

        Response:
            {
                "run": {...},
                "candidates": [...]
            }

        The returned candidates are isolated to the DiscoveryRun that was just
        created, so the frontend does not mix results from previous runs.
        """
        serializer = RunBondDiscoverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            discovery_run = run_bond_discovery(
                user=request.user,
                source=serializer.validated_data.get("source"),
                min_rating=serializer.validated_data.get("min_rating"),
                currencies=serializer.validated_data.get("currencies"),
                countries=serializer.validated_data.get("countries"),
                bond_types=serializer.validated_data.get("bond_types"),
            )
        except DiscoveryServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        visible_candidates = (
            get_visible_candidates(user=request.user)
            .filter(discovery_run=discovery_run)
            .select_related(
                "user",
                "discovery_run",
            )
        )

        return Response(
            {
                "run": DiscoveryRunSerializer(discovery_run).data,
                "candidates": BondCandidateSerializer(
                    visible_candidates,
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="clear-current")
    def clear_current(self, request):
        """
        Clear currently visible discovery results.

        This does not delete records from the database.
        It marks visible candidates as IGNORED.

        Request payload:
            {
                "discovery_run_id": 12
            }

        If discovery_run_id is provided, only visible candidates from that run
        are ignored.

        If discovery_run_id is omitted, all currently visible candidates for the
        authenticated user are ignored.

        This action does not affect:
        - Portfolio items
        - Watchlist items
        - candidates already added to Watchlist
        """
        discovery_run_id = request.data.get(
            "discovery_run_id",
        ) or request.query_params.get(
            "discovery_run_id",
        )

        queryset = get_visible_candidates(user=request.user)

        if discovery_run_id:
            discovery_run_id_as_text = str(discovery_run_id)

            if not discovery_run_id_as_text.isdigit():
                return Response(
                    {"detail": "discovery_run_id must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(
                discovery_run_id=int(discovery_run_id_as_text),
                discovery_run__user=request.user,
            )

        ignored_count = queryset.update(
            status=BondCandidate.Status.IGNORED,
            updated_at=timezone.now(),
        )

        return Response(
            {
                "detail": "Current discovery results cleared.",
                "ignored_count": ignored_count,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="add-to-watchlist")
    def add_to_watchlist(self, request, pk=None):
        """
        Add a discovered candidate to the authenticated user's Watchlist.

        The service:
        - creates Bond master data if needed
        - creates or updates market data if candidate market price exists
        - creates or reactivates a WATCHLIST UserBond
        - marks the candidate as ADDED_TO_WATCHLIST
        """
        try:
            watchlist_item = add_candidate_to_watchlist(
                user=request.user,
                candidate_id=pk,
            )
        except BondCandidate.DoesNotExist:
            return Response(
                {"detail": "Candidate was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DiscoveryServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Candidate added to Watchlist.",
                "user_bond_id": watchlist_item.id,
                "bond_id": watchlist_item.bond_id,
                "isin": watchlist_item.bond.isin,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="ignore")
    def ignore(self, request, pk=None):
        """
        Ignore a discovered candidate.

        Ignored candidates are no longer visible in Discover Bonds and should
        not be recreated by future discovery runs for the same user/ISIN.
        """
        try:
            candidate = ignore_candidate(
                user=request.user,
                candidate_id=pk,
            )
        except BondCandidate.DoesNotExist:
            return Response(
                {"detail": "Candidate was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "detail": "Candidate ignored.",
                "candidate": BondCandidateSerializer(candidate).data,
            },
            status=status.HTTP_200_OK,
        )


