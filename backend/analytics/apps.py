"""
Application configuration for the analytics app.
"""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """
    Analytics app configuration.

    The ready method imports signal handlers so automatic analysis is enabled
    when Django starts.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"
    verbose_name = "Analytics"

    def ready(self):
        """
        Import signal handlers.

        This import is intentionally placed inside ready() so signal receivers
        are registered after Django loads the application registry.
        """
        import analytics.signals  # noqa: F401