from django.core.management.base import BaseCommand

from apps.notifications.services import send_pending, send_pending_user_messages


class Command(BaseCommand):
    help = "Navbatdagi xabarlar: adminlarga Telegram, foydalanuvchilarga email/SMS (scheduler, 15 s)."

    def handle(self, *args, **options):
        sent, failed = send_pending()
        if sent or failed:
            self.stdout.write(f"telegram: yuborildi {sent}, xato {failed}")
        sent, failed = send_pending_user_messages()
        if sent or failed:
            self.stdout.write(f"email/sms: yuborildi {sent}, xato {failed}")
