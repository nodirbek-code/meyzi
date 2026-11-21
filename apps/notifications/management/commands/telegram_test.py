from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.notifications import telegram


class Command(BaseCommand):
    help = "Barcha admin chatlariga sinov xabarini darhol yuboradi."

    def handle(self, *args, **options):
        if not telegram.is_configured():
            raise CommandError("TELEGRAM_BOT_TOKEN va TELEGRAM_ADMIN_CHAT_IDS ni .env ga yozing.")
        for chat_id in settings.TELEGRAM_ADMIN_CHAT_IDS:
            try:
                telegram.send_message(
                    chat_id, f"✅ <b>{settings.BRAND_NAME}</b>: Telegram bildirishnomalari ishlayapti."
                )
                self.stdout.write(self.style.SUCCESS(f"{chat_id}: yuborildi"))
            except telegram.TelegramError as exc:
                self.stdout.write(self.style.ERROR(f"{chat_id}: {exc}"))
