from django.core.management.base import BaseCommand

from apps.core.inventory import fill_all


class Command(BaseCommand):
    help = (
        "Platforma yozuvlarida yo'q narsani to'ldiradi: turlarga haftaning barcha kunlariga sanalar, "
        "mehmonxonalarga xona turlari, gidlarga uchrashuv joylari. Idempotent — har deployda."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=120, help="Necha kun oldinga sanalar (default: 120)")

    def handle(self, *args, days, **options):
        r = fill_all(days=days)
        self.stdout.write(
            f"inventory: +{r['departures']} jo'nash sanasi, +{r['rooms']} xona turi, "
            f"+{r['meeting_points']} uchrashuv joyi"
        )
