from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone
from datetime import timedelta

from meters.models import MeterReading


class Command(BaseCommand):
    help = "Delete MeterReading rows older than N days (default: 7)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Retention in days. Rows older than this are deleted.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        qs = MeterReading.objects.filter(time__lt=cutoff)
        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {deleted} MeterReading rows older than {days} days (cutoff {cutoff})."
        ))
