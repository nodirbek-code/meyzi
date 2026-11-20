from django.core.management.base import BaseCommand

from apps.bookings import services
from apps.guides import services as guide_services
from apps.hotels import services as hotel_services


class Command(BaseCommand):
    help = (
        "Fon vazifasi: to'lov muddati o'tgan bronlarni expired qiladi (joylar qaytadi) "
        "va tugagan sayohatlarni completed qiladi (turlar, gidlar, mehmonxonalar). "
        "Muntazam ishga tushiring (cron yoki keyinchalik Celery beat)."
    )

    def handle(self, *args, **options):
        expired = (
            services.expire_due_bookings() + guide_services.expire_requests() + hotel_services.expire_due()
        )
        completed = (
            services.complete_finished_bookings()
            + guide_services.complete_finished()
            + hotel_services.complete_finished()
        )
        if expired or completed or options["verbosity"] > 1:
            self.stdout.write(f"expired: {expired}, completed: {completed}")
