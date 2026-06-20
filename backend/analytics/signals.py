"""
Django signals for automatic bond analysis recalculation.

These signals ensure that analysis is recalculated automatically when:
- New market data is saved.
- A user's Portfolio or Watchlist item is created or updated.

The user never needs to press a "Run Analysis" button.
"""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from bonds.models import BondMarketData
from portfolios.models import UserBond

from .services import analyze_bond_for_all_users, analyze_user_bond


@receiver(post_save, sender=BondMarketData)
def recalculate_analysis_after_market_data_save(sender, instance, **kwargs):
    """
    Recalculate analysis for all active users when market data changes.

    Args:
        sender: Signal sender model.
        instance: Saved BondMarketData instance.
        kwargs: Extra signal arguments.
    """

    def run_after_commit():
        analyze_bond_for_all_users(
            bond=instance.bond,
            market_data=instance,
        )

    transaction.on_commit(run_after_commit)


@receiver(post_save, sender=UserBond)
def recalculate_analysis_after_user_bond_save(sender, instance, **kwargs):
    """
    Recalculate analysis when a user's Portfolio or Watchlist item changes.

    Args:
        sender: Signal sender model.
        instance: Saved UserBond instance.
        kwargs: Extra signal arguments.
    """

    def run_after_commit():
        analyze_user_bond(user_bond=instance)

    transaction.on_commit(run_after_commit)