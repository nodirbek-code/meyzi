"""Docker'siz lokal ishga tushirish uchun: docker-compose'dagi `scheduler` xizmatining o'rnini bosadi.

Har N soniyada `process_bookings` va `send_notifications` ni chaqiradi.
"""

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bronlarni qayta ishlash va bildirishnomalarni yuborishni siklda bajaradi (lokal dev)."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=15, help="Soniyalar (default: 15)")

    def handle(self, *args, interval, **options):
        self.stdout.write(f"Scheduler ishga tushdi, har {interval} soniyada. To'xtatish: Ctrl+C")
        try:
            while True:
                for cmd in ("process_bookings", "send_notifications"):
                    try:
                        call_command(cmd)
                    except Exception as exc:  # noqa: BLE001 — sikl to'xtamasin
                        self.stderr.write(f"{cmd} xatosi: {exc}")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write("Scheduler to'xtatildi.")
