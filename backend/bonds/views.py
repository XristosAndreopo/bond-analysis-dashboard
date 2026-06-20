"""
API views for bonds, market data, and FX rates.

Market data and FX rates use an upsert-style behavior. If a record already
exists for the same unique fields, it is updated instead of returning a
duplicate unique constraint error.
"""

from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Bond, BondMarketData, FXRate
from .serializers import BondMarketDataSerializer, BondSerializer, FXRateSerializer


class BondViewSet(ModelViewSet):
    """
    API endpoint for bond master data.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BondSerializer

    def get_queryset(self):
        """
        Return bonds filtered by optional search query.
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
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BondMarketDataSerializer

    def get_queryset(self):
        """
        Return market data filtered by optional bond id.
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

        If a record exists for the same bond, quote_date, and source, update it.
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

        If a record exists for the same:
        - base_currency
        - quote_currency
        - rate_date
        - source

        update it instead of creating duplicate data.
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