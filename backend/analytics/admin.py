"""
Django admin configuration for analysis models.
"""

from django.contrib import admin

from .models import BondAnalysis, CashFlow


class CashFlowInline(admin.TabularInline):
    """
    Inline cash flow table inside a BondAnalysis admin page.
    """

    model = CashFlow
    extra = 0
    readonly_fields = (
        "period_number",
        "payment_date",
        "coupon_gross",
        "coupon_tax",
        "coupon_net",
        "principal",
        "total_cash_flow",
        "discounted_cash_flow",
    )


@admin.register(BondAnalysis)
class BondAnalysisAdmin(admin.ModelAdmin):
    """
    Admin interface for calculated bond analysis records.
    """

    list_display = (
        "user_bond",
        "analysis_date",
        "risk_score",
        "risk_level",
        "final_signal",
        "position_value",
        "updated_at",
    )
    list_filter = (
        "analysis_date",
        "risk_level",
        "final_signal",
    )
    search_fields = (
        "user_bond__user__username",
        "user_bond__bond__isin",
        "user_bond__bond__name",
    )
    ordering = (
        "-analysis_date",
        "-created_at",
    )
    inlines = [CashFlowInline]


@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    """
    Admin interface for calculated cash flow rows.
    """

    list_display = (
        "analysis",
        "period_number",
        "payment_date",
        "coupon_gross",
        "coupon_tax",
        "coupon_net",
        "principal",
        "total_cash_flow",
        "discounted_cash_flow",
    )
    list_filter = (
        "payment_date",
    )
    search_fields = (
        "analysis__user_bond__bond__isin",
        "analysis__user_bond__bond__name",
    )
    ordering = (
        "analysis",
        "period_number",
    )