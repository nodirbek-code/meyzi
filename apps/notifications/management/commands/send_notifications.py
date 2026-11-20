from django.core.management.base import BaseCommand

from apps.notifications.services import send_pending


class Command(BaseCommand):
    help = "Navbatdagi Telegram xabarlarini adminlarga yuboradi (scheduler har 15 soniyada chaqiradi)."

    def handle(self, *args, **options):
        sent, failed = send_pending()
        if sent or failed:
            self.stdout.write(f"telegram: yuborildi {sent}, xato {failed}")
