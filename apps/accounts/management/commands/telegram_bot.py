import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.accounts import telegram_bot
from apps.notifications import telegram

POLL_TIMEOUT = 25


class Command(BaseCommand):
    help = (
        "Telegram botni ishga tushiradi: saytga ro'yxatdan o'tish/kirish (long polling — dev uchun). "
        "Prod'da webhook: --set-webhook https://<domen>/api/v1/auth/telegram/webhook/"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--set-webhook", metavar="URL", help="Webhook o'rnatish (TELEGRAM_WEBHOOK_SECRET kerak)"
        )
        parser.add_argument("--delete-webhook", action="store_true", help="Webhook'ni o'chirish")

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN sozlanmagan (.env). Tokenni @BotFather beradi.")
        try:
            me = telegram.call("getMe")
        except telegram.TelegramError as exc:
            raise CommandError(f"Bot bilan bog'lanib bo'lmadi: {exc}") from None
        username = me.get("username", "")
        self.stdout.write(f"Bot: @{username}")
        if settings.TELEGRAM_BOT_USERNAME.lower() != username.lower():
            self.stderr.write(
                self.style.WARNING(
                    f".env da TELEGRAM_BOT_USERNAME={username} yozing — aks holda saytdagi tugma ishlamaydi."
                )
            )

        if options["set_webhook"]:
            if not settings.TELEGRAM_WEBHOOK_SECRET:
                raise CommandError("TELEGRAM_WEBHOOK_SECRET sozlanmagan (.env).")
            telegram.call(
                "setWebhook",
                {
                    "url": options["set_webhook"],
                    "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
                    "allowed_updates": ["message"],
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Webhook o'rnatildi: {options['set_webhook']}"))
            return
        if options["delete_webhook"]:
            telegram.call("deleteWebhook")
            self.stdout.write(self.style.SUCCESS("Webhook o'chirildi."))
            return

        info = telegram.call("getWebhookInfo")
        if info.get("url"):
            raise CommandError(
                f"Botda webhook o'rnatilgan ({info['url']}) — long polling ishlamaydi. "
                "Dev uchun avval: python manage.py telegram_bot --delete-webhook"
            )
        self.stdout.write(self.style.SUCCESS("Bot ishlayapti. To'xtatish: Ctrl+C"))
        self._poll()

    def _poll(self):
        offset = None
        while True:
            try:
                updates = telegram.call(
                    "getUpdates",
                    {"timeout": POLL_TIMEOUT, "offset": offset, "allowed_updates": ["message"]},
                    timeout=POLL_TIMEOUT + 10,
                )
            except KeyboardInterrupt:
                self.stdout.write("To'xtatildi.")
                return
            except telegram.TelegramError as exc:
                self.stderr.write(f"Telegram xatosi: {exc} — 5 soniyadan keyin qayta urinaman")
                time.sleep(5)
                continue
            for update in updates:
                offset = update["update_id"] + 1
                close_old_connections()
                telegram_bot.process_update(update)
