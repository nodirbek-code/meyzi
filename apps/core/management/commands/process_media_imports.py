from django.core.management.base import BaseCommand

from apps.core.media_import import process_pending


class Command(BaseCommand):
    help = "ZIP media importlarini qismlab ishlaydi (scheduler har siklda chaqiradi)."

    def add_arguments(self, parser):
        parser.add_argument("--seconds", type=float, default=20, help="Bir chaqiruvdagi vaqt chegarasi")

    def handle(self, *args, seconds, **options):
        done = process_pending(seconds=seconds)
        if done:
            self.stdout.write(f"media import: {done} qism")
