"""
API views for Dashboard, Portfolio, Watchlist, and bond detail pages.

The API is designed around a simple user flow:
- The user logs in.
- The user views Dashboard, Portfolio, and Watchlist.
- The user can add a bond to Portfolio or Watchlist.
- If the same bond exists in the opposite section, it is moved instead of
  duplicated.
- If an inactive target record exists, it is reactivated instead of creating
  a duplicate.
- Analysis is recalculated automatically through model signals.

Portfolio and Watchlist financial values are calculated in the backend.
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.portfolio_services import calculate_portfolio_analytics
from analytics.watchlist_services import calculate_watchlist_analytics
from portfolios.models import UserBond
from portfolios.serializers import (
    MoveUserBondSerializer,
    PortfolioRowSerializer,
    UserBondReadSerializer,
    UserBondWriteSerializer,
    WatchlistRowSerializer,
)
from portfolios.services import calculate_portfolio_summary


DISCLAIMER_TEXT = (
    "Οι ενδείξεις της εφαρμογής είναι εκπαιδευτικές/αναλυτικές και δεν "
    "αποτελούν επενδυτική συμβουλή ή προτροπή αγοράς/πώλησης."
)


def get_opposite_holding_type(holding_type):
    """
    Return the opposite holding type.

    Args:
        holding_type: Current holding type.

    Returns:
        Opposite UserBond holding type.
    """
    if holding_type == UserBond.HoldingType.PORTFOLIO:
        return UserBond.HoldingType.WATCHLIST

    return UserBond.HoldingType.PORTFOLIO


def decimal_to_string(value):
    """
    Convert a Decimal-like value to string for stable JSON output.

    Args:
        value: Decimal-like value.

    Returns:
        String value or None.
    """
    if value is None:
        return None

    return str(value)


def serialize_distribution(distribution_rows):
    """
    Serialize signal/risk distribution rows.

    Args:
        distribution_rows: Distribution rows from analytics service.

    Returns:
        List of serializable dictionaries.
    """
    return [
        {
            "key": row["key"],
            "label": row["label"],
            "count": row["count"],
        }
        for row in distribution_rows
    ]


def serialize_currency_rows(rows):
    """
    Serialize currency exposure or coupon-income rows.

    Args:
        rows: Currency rows from analytics service.

    Returns:
        List of serializable dictionaries.
    """
    serialized_rows = []

    for row in rows:
        serialized_row = {
            "currency": row["currency"],
        }

        if "value" in row:
            serialized_row["value"] = decimal_to_string(row["value"])

        if "original_value" in row:
            serialized_row["original_value"] = decimal_to_string(
                row["original_value"]
            )

        if "converted_value" in row:
            serialized_row["converted_value"] = decimal_to_string(
                row["converted_value"]
            )

        if "portfolio_base_currency" in row:
            serialized_row["portfolio_base_currency"] = row[
                "portfolio_base_currency"
            ]

        if "weight" in row:
            serialized_row["weight"] = decimal_to_string(row["weight"])

        serialized_rows.append(serialized_row)

    return serialized_rows


def serialize_position_insight(normalized_item, metric_key):
    """
    Serialize a portfolio insight position.

    Args:
        normalized_item: Normalized portfolio item from service.
        metric_key: Metric key to expose.

    Returns:
        Serialized insight dict or None.
    """
    if normalized_item is None:
        return None

    return {
        "item": UserBondReadSerializer(normalized_item["item"]).data,
        metric_key: decimal_to_string(normalized_item.get(metric_key)),
    }


def serialize_portfolio_metrics(metrics):
    """
    Serialize portfolio metrics calculated by the backend.

    Args:
        metrics: Metrics dictionary from portfolio service.

    Returns:
        Serializable metrics dictionary.
    """
    return {
        "portfolio_base_currency": metrics["portfolio_base_currency"],
        "total_value_base": decimal_to_string(metrics["total_value_base"]),
        "weighted_average_ytm": decimal_to_string(
            metrics["weighted_average_ytm"]
        ),
        "weighted_current_yield": decimal_to_string(
            metrics["weighted_current_yield"]
        ),
        "weighted_modified_duration": decimal_to_string(
            metrics["weighted_modified_duration"]
        ),
        "weighted_risk_score": decimal_to_string(
            metrics["weighted_risk_score"]
        ),
        "portfolio_concentration": decimal_to_string(
            metrics["portfolio_concentration"]
        ),
        "estimated_annual_coupon_income": decimal_to_string(
            metrics["estimated_annual_coupon_income"]
        ),
        "estimated_annual_coupon_income_by_currency": serialize_currency_rows(
            metrics["estimated_annual_coupon_income_by_currency"]
        ),
        "main_currency": metrics["main_currency"],
        "has_mixed_currencies": metrics["has_mixed_currencies"],
        "has_missing_fx_rates": metrics["has_missing_fx_rates"],
        "missing_fx_rates": metrics["missing_fx_rates"],
        "currency_exposure": serialize_currency_rows(
            metrics["currency_exposure"]
        ),
        "top_position": serialize_position_insight(
            metrics["top_position"],
            "weight",
        ),
        "highest_risk_position": serialize_position_insight(
            metrics["highest_risk_position"],
            "risk_score",
        ),
        "best_value_position": serialize_position_insight(
            metrics["best_value_position"],
            "iv_vs_market_price",
        ),
        "signal_distribution": serialize_distribution(
            metrics["signal_distribution"]
        ),
        "risk_distribution": serialize_distribution(
            metrics["risk_distribution"]
        ),
        "mixed_currency_warning": metrics["mixed_currency_warning"],
    }


def create_update_or_move_user_bond(request, target_holding_type):
    """
    Create, update, move, or reactivate a user bond item.

    This function prevents the same active bond from appearing in both
    Portfolio and Watchlist for the same user.

    Important:
        Because older inactive rows may exist in the database, this function
        reactivates an inactive target row instead of creating a duplicate.
        This prevents unique constraint errors when moving a bond back to a
        section where it existed before.
    """
    bond_id = request.data.get("bond")

    if not bond_id:
        serializer = UserBondWriteSerializer(
            data=request.data,
            context={
                "request": request,
                "forced_holding_type": target_holding_type,
            },
        )
        serializer.is_valid(raise_exception=True)

        return serializer.save(), status.HTTP_201_CREATED

    opposite_holding_type = get_opposite_holding_type(target_holding_type)

    target_active_item = UserBond.objects.filter(
        user=request.user,
        bond_id=bond_id,
        holding_type=target_holding_type,
        is_active=True,
    ).first()

    target_inactive_item = UserBond.objects.filter(
        user=request.user,
        bond_id=bond_id,
        holding_type=target_holding_type,
        is_active=False,
    ).first()

    opposite_active_item = UserBond.objects.filter(
        user=request.user,
        bond_id=bond_id,
        holding_type=opposite_holding_type,
        is_active=True,
    ).first()

    with transaction.atomic():
        if target_active_item is not None:
            updated_item = update_user_bond_from_request(
                request=request,
                instance=target_active_item,
                target_holding_type=target_holding_type,
                reactivate=True,
            )

            if opposite_active_item is not None:
                deactivate_user_bond(opposite_active_item)

            return updated_item, status.HTTP_200_OK

        if target_inactive_item is not None:
            reactivated_item = update_user_bond_from_request(
                request=request,
                instance=target_inactive_item,
                target_holding_type=target_holding_type,
                reactivate=True,
            )

            if opposite_active_item is not None:
                deactivate_user_bond(opposite_active_item)

            return reactivated_item, status.HTTP_200_OK

        if opposite_active_item is not None:
            moved_item = update_user_bond_from_request(
                request=request,
                instance=opposite_active_item,
                target_holding_type=target_holding_type,
                reactivate=True,
            )

            return moved_item, status.HTTP_200_OK

        serializer = UserBondWriteSerializer(
            data=request.data,
            context={
                "request": request,
                "forced_holding_type": target_holding_type,
            },
        )
        serializer.is_valid(raise_exception=True)

        return serializer.save(), status.HTTP_201_CREATED


def update_user_bond_from_request(
    request,
    instance,
    target_holding_type,
    reactivate=False,
):
    """
    Update a UserBond instance using request data.

    Args:
        request: DRF request.
        instance: UserBond instance.
        target_holding_type: Target section.
        reactivate: Whether to force is_active=True.

    Returns:
        Updated UserBond instance.
    """
    serializer = UserBondWriteSerializer(
        instance,
        data=request.data,
        partial=True,
        context={
            "request": request,
            "forced_holding_type": target_holding_type,
        },
    )
    serializer.is_valid(raise_exception=True)

    extra_save_kwargs = {
        "holding_type": target_holding_type,
    }

    if reactivate:
        extra_save_kwargs["is_active"] = True

    return serializer.save(**extra_save_kwargs)


def deactivate_user_bond(user_bond):
    """
    Deactivate a UserBond item.

    Args:
        user_bond: UserBond instance.
    """
    user_bond.is_active = False
    user_bond.save(update_fields=["is_active", "updated_at"])


class UserBondQuerysetMixin:
    """
    Shared queryset helper for user-owned Portfolio and Watchlist items.
    """

    def get_user_bond_queryset(self):
        """
        Return active UserBond records owned by the authenticated user.
        """
        return UserBond.objects.filter(
            user=self.request.user,
            is_active=True,
        ).select_related(
            "user",
            "bond",
        ).prefetch_related(
            "analyses",
            "analyses__cash_flows",
        )


class DashboardAPIView(UserBondQuerysetMixin, APIView):
    """
    API endpoint for the main dashboard.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return dashboard data for the current user.
        """
        portfolio_items = self.get_user_bond_queryset().filter(
            holding_type=UserBond.HoldingType.PORTFOLIO,
        )

        serializer = UserBondReadSerializer(
            portfolio_items,
            many=True,
        )

        return Response(
            {
                "disclaimer": DISCLAIMER_TEXT,
                "summary": calculate_portfolio_summary(request.user),
                "portfolio_items": serializer.data,
            }
        )


class PortfolioAPIView(UserBondQuerysetMixin, APIView):
    """
    API endpoint for the Portfolio page.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return Portfolio items and backend-calculated metrics.
        """
        portfolio_base_currency = request.query_params.get(
            "base_currency",
            "EUR",
        )

        portfolio_analytics = calculate_portfolio_analytics(
            user=request.user,
            portfolio_base_currency=portfolio_base_currency,
        )

        row_serializer = PortfolioRowSerializer(
            portfolio_analytics["rows"],
            many=True,
        )

        return Response(
            {
                "disclaimer": DISCLAIMER_TEXT,
                "summary": portfolio_analytics["summary"],
                "portfolio_metrics": serialize_portfolio_metrics(
                    portfolio_analytics["metrics"]
                ),
                "items": row_serializer.data,
            }
        )

    def post(self, request):
        """
        Create, update, move, or reactivate a bond into Portfolio.
        """
        user_bond, response_status = create_update_or_move_user_bond(
            request=request,
            target_holding_type=UserBond.HoldingType.PORTFOLIO,
        )

        read_serializer = UserBondReadSerializer(user_bond)

        return Response(
            read_serializer.data,
            status=response_status,
        )


class WatchlistAPIView(UserBondQuerysetMixin, APIView):
    """
    API endpoint for the Watchlist page.

    GET returns FX-aware Watchlist rows.
    POST creates, updates, moves, or reactivates a bond into Watchlist.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return Watchlist items with FX-aware market price data.
        """
        portfolio_base_currency = request.query_params.get(
            "base_currency",
            "EUR",
        )

        watchlist_analytics = calculate_watchlist_analytics(
            user=request.user,
            portfolio_base_currency=portfolio_base_currency,
        )

        row_serializer = WatchlistRowSerializer(
            watchlist_analytics["rows"],
            many=True,
        )

        return Response(
            {
                "disclaimer": DISCLAIMER_TEXT,
                "watchlist_metrics": watchlist_analytics["metrics"],
                "items": row_serializer.data,
            }
        )

    def post(self, request):
        """
        Create, update, move, or reactivate a bond into Watchlist.
        """
        user_bond, response_status = create_update_or_move_user_bond(
            request=request,
            target_holding_type=UserBond.HoldingType.WATCHLIST,
        )

        read_serializer = UserBondReadSerializer(user_bond)

        return Response(
            read_serializer.data,
            status=response_status,
        )


class UserBondDetailAPIView(
    UserBondQuerysetMixin,
    RetrieveUpdateDestroyAPIView,
):
    """
    API endpoint for one Portfolio or Watchlist item.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return user-owned active bond items.
        """
        return self.get_user_bond_queryset()

    def get_serializer_class(self):
        """
        Use read serializer for GET and write serializer for updates.
        """
        if self.request.method == "GET":
            return UserBondReadSerializer

        return UserBondWriteSerializer

    def get_serializer_context(self):
        """
        Pass request context to serializers.
        """
        context = super().get_serializer_context()
        context["request"] = self.request

        return context

    def retrieve(self, request, *args, **kwargs):
        """
        Return detailed data for one user bond.
        """
        instance = self.get_object()
        serializer = UserBondReadSerializer(instance)

        return Response(
            {
                "disclaimer": DISCLAIMER_TEXT,
                "item": serializer.data,
            }
        )

    def update(self, request, *args, **kwargs):
        """
        Update one user bond and return the read representation.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = UserBondWriteSerializer(
            instance,
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        read_serializer = UserBondReadSerializer(updated_instance)

        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Soft-delete the item by marking it inactive.
        """
        instance = self.get_object()
        deactivate_user_bond(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class MoveUserBondAPIView(UserBondQuerysetMixin, APIView):
    """
    API endpoint for moving a bond between Portfolio and Watchlist.

    This view handles the important case where an inactive record already
    exists in the target section. In that case, the inactive target record is
    reactivated and the source record is deactivated.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        Move a user bond to Portfolio or Watchlist.
        """
        source_item = get_object_or_404(
            self.get_user_bond_queryset(),
            pk=pk,
        )

        serializer = MoveUserBondSerializer(
            data=request.data,
            context={"user_bond": source_item},
        )
        serializer.is_valid(raise_exception=True)

        target_holding_type = serializer.validated_data["target_holding_type"]

        existing_target = UserBond.objects.filter(
            user=request.user,
            bond=source_item.bond,
            holding_type=target_holding_type,
        ).exclude(
            pk=source_item.pk,
        ).first()

        with transaction.atomic():
            if existing_target is not None:
                target_item = self._reactivate_or_update_existing_target(
                    existing_target=existing_target,
                    source_item=source_item,
                    validated_data=serializer.validated_data,
                    target_holding_type=target_holding_type,
                )
            else:
                target_item = self._move_current_item(
                    source_item=source_item,
                    target_holding_type=target_holding_type,
                    validated_data=serializer.validated_data,
                )

        read_serializer = UserBondReadSerializer(target_item)

        return Response(read_serializer.data)

    def _reactivate_or_update_existing_target(
        self,
        existing_target,
        source_item,
        validated_data,
        target_holding_type,
    ):
        """
        Reactivate or update an existing target item.

        Args:
            existing_target: Existing active or inactive target record.
            source_item: Current active source record.
            validated_data: Move request data.
            target_holding_type: Target holding type.

        Returns:
            Reactivated or updated target item.
        """
        existing_target.is_active = True
        existing_target.holding_type = target_holding_type

        if target_holding_type == UserBond.HoldingType.PORTFOLIO:
            existing_target.quantity = validated_data.get(
                "quantity",
                existing_target.quantity or 1,
            )
            existing_target.purchase_price = validated_data.get(
                "purchase_price",
                existing_target.purchase_price,
            )
        else:
            existing_target.quantity = 0
            existing_target.purchase_price = None

        existing_target.save()

        deactivate_user_bond(source_item)

        return existing_target

    def _move_current_item(
        self,
        source_item,
        target_holding_type,
        validated_data,
    ):
        """
        Move the current item to the target section.

        This path is used only when no target record exists at all.
        """
        source_item.holding_type = target_holding_type
        source_item.is_active = True

        if target_holding_type == UserBond.HoldingType.PORTFOLIO:
            source_item.quantity = validated_data.get(
                "quantity",
                source_item.quantity or 1,
            )
            source_item.purchase_price = validated_data.get(
                "purchase_price",
                source_item.purchase_price,
            )
        else:
            source_item.quantity = 0
            source_item.purchase_price = None

        source_item.save()

        return source_item