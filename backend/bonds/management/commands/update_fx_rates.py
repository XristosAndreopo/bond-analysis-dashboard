"""
Management command for updating live FX rates.

Usage examples:

    python manage.py update_fx_rates

    python manage.py update_fx_rates --quote EUR --base USD GBP CHF

    python manage.py update_fx_rates --quote USD --base EUR GBP

The command stores the latest available provider rate in the FXRate table.
"""

from django.core.management.base import BaseCommand, CommandError

from bonds.fx_services import FXRateUpdateError, update_latest_fx_rates


class Command(BaseCommand):
    """
    Update FX rates from Frankfurter public API.
    """

    help = "Fetch latest FX rates and store them in the database."

    def add_arguments(self, parser):
        """
        Add command-line arguments.
        """
        parser.add_argument(
            "--quote",
            default="EUR",
            help="Quote/target currency. Default: EUR.",
        )
        parser.add_argument(
            "--base",
            nargs="+",
            default=["USD", "GBP", "CHF", "JPY", "CAD", "AUD"],
            help=(
                "Base/source currencies to convert from. "
                "Example: --base USD GBP CHF"
            ),
        )

    def handle(self, *args, **options):
        """
        Execute the FX update command.
        """
        quote_currency = options["quote"]
        base_currencies = options["base"]

        self.stdout.write(
            self.style.NOTICE(
                f"Updating FX rates to {quote_currency.upper()}..."
            )
        )

        try:
            result = update_latest_fx_rates(
                quote_currency=quote_currency,
                base_currencies=base_currencies,
            )
        except FXRateUpdateError as exc:
            raise CommandError(str(exc)) from exc

        updated = result["updated"]
        errors = result["errors"]

        for item in updated:
            action = "created" if item.created else "updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{item.base_currency}/{item.quote_currency} "
                    f"{item.rate_date}: {item.rate} ({action})"
                )
            )

        for error in errors:
            self.stdout.write(
                self.style.WARNING(error)
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"FX update completed. Updated: {len(updated)}, "
                f"Errors: {len(errors)}"
            )
        )