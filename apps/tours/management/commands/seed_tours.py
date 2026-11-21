from datetime import time, timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.agencies.models import Agency
from apps.catalog.models import Destination
from apps.tours.models import CancellationPolicy, Departure, ItineraryDay, ItineraryItem, Tour, TourCategory

CATEGORIES = [
    ("tog", "Tog'", "⛰️", 1),
    ("madaniy", "Madaniy", "🕌", 2),
    ("sarguzasht", "Sarguzasht", "🧗", 3),
    ("dam-olish-kuni", "Dam olish kuni", "🌤️", 4),
]

EXTRA_DESTINATIONS = [
    ("chimyon", "Chimyon", "Toshkent viloyati", "Toshkentdan 1,5 soatlik tog' kurorti."),
    ("zomin", "Zomin", "Jizzax viloyati", "Archazorlar, Turkiston tizmasi va milliy bog'."),
    ("chorvoq", "Chorvoq", "Toshkent viloyati", "Tog'lar orasidagi moviy suv ombori."),
]

# (slug, nomi, yo'nalish, toifalar, kunlar, kechalar, narx, siyosat, dastur)
TOURS = [
    (
        "chimyon-1-kunlik-sayohat",
        "Chimyon — 1 kunlik tog' sayohati",
        "chimyon",
        ["tog", "dam-olish-kuni"],
        1,
        0,
        250_000,
        CancellationPolicy.FREE,
        {
            1: [
                ("07:00", "07:30", "Toshkentda yig'ilish", False),
                ("07:30", "09:00", "Chimyonga yo'l", False),
                ("09:00", "13:00", "Kanatli yo'l va Katta Chimyon etagida sayr", False),
                ("13:00", "14:00", "Tushlik", True),
                ("14:00", "17:00", "Chorvoq bo'yida dam olish", False),
                ("17:00", "19:00", "Toshkentga qaytish", False),
            ]
        },
    ),
    (
        "samarqand-1-kunlik-poyezdda",
        "Samarqand — 1 kunda Afrosiyob poyezdida",
        "samarqand",
        ["madaniy"],
        1,
        0,
        950_000,
        CancellationPolicy.PARTIAL,
        {
            1: [
                ("06:30", "08:40", "Afrosiyob poyezdi: Toshkent → Samarqand", False),
                ("09:00", "11:00", "Registon maydoni (gid bilan)", False),
                ("11:00", "12:30", "Shohi Zinda majmuasi", False),
                ("12:30", "13:30", "Samarqand oshi", False),
                ("13:30", "15:00", "Bibixonim masjidi va Siyob bozori", False),
                ("17:00", "19:10", "Toshkentga qaytish", False),
            ]
        },
    ),
    (
        "zomin-2-kun-1-kecha",
        "Zomin — 2 kun / 1 kecha tog'larda",
        "zomin",
        ["tog", "sarguzasht"],
        2,
        1,
        890_000,
        CancellationPolicy.FREE,
        {
            1: [
                ("06:00", "06:30", "Toshkentda yig'ilish", False),
                ("06:30", "10:00", "Zominga yo'l", False),
                ("11:00", "12:00", "Tushlik", True),
                ("14:00", "19:00", "Mehmonxonaga joylashish va dam olish", False),
                ("19:00", "20:00", "Kechki ovqat", False),
            ],
            2: [
                ("07:00", "08:30", "Nonushta", False),
                ("08:45", "11:00", "Chortang kanyoni bo'ylab piyoda sayr (gid bilan)", False),
                ("15:00", "15:30", "Zomin patiri master-klassi", False),
                ("16:00", "19:30", "Toshkentga qaytish", False),
            ],
        },
    ),
]


def _t(value):
    h, m = value.split(":")
    return time(int(h), int(m))


class Command(BaseCommand):
    help = "Demo: toifalar, platforma agentligi, 3 ta tur va kelgusi shanbalarga jo'nash sanalari."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_catalog", verbosity=0)

        for slug, name, icon, order in CATEGORIES:
            TourCategory.objects.update_or_create(
                slug=slug, defaults={"name": name, "icon": icon, "sort_order": order}
            )

        for slug, name, region, desc in EXTRA_DESTINATIONS:
            Destination.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "region": region, "short_description": desc, "sort_order": 10},
            )

        lazuri, _ = Agency.objects.update_or_create(
            slug="lazuri",
            defaults={
                "name": settings.BRAND_NAME,
                "description": f"{settings.BRAND_NAME} platformasining o'z turlari.",
                "is_platform": True,
                "is_verified": True,
                "auto_publish": True,
                "commission_percent": 0,
            },
        )

        today = timezone.localdate()
        first_saturday = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
        created = 0
        for slug, title, dest, cats, days, nights, price, policy, program in TOURS:
            tour, is_new = Tour.objects.update_or_create(
                slug=slug,
                defaults={
                    "agency": lazuri,
                    "destination": Destination.objects.get(slug=dest),
                    "title": title,
                    "duration_days": days,
                    "duration_nights": nights,
                    "price_uzs": price,
                    "cancellation_policy": policy,
                    "max_group_size": 20,
                    "departure_time": _t(program[1][0][0]),
                    "meeting_point": "Toshkent, Amir Temur xiyoboni",
                    "meeting_latitude": "41.311151",
                    "meeting_longitude": "69.279737",
                    "included": ["Transport", "Gid", "Kirish chiptalari"],
                    "not_included": ["Tushlik", "Shaxsiy xarajatlar"],
                    "what_to_bring": ["Pasport", "Qulay poyabzal", "Issiq kiyim"],
                },
            )
            created += is_new
            tour.categories.set(TourCategory.objects.filter(slug__in=cats))
            tour.publish()
            tour.save()

            tour.itinerary.all().delete()
            for day_number, items in program.items():
                day = ItineraryDay.objects.create(tour=tour, day_number=day_number, title=f"{day_number}-kun")
                ItineraryItem.objects.bulk_create(
                    ItineraryItem(
                        day=day, start_time=_t(s), end_time=_t(e), title=t, is_extra_cost=x, sort_order=i
                    )
                    for i, (s, e, t, x) in enumerate(items)
                )
            for week in range(6):
                Departure.objects.get_or_create(
                    tour=tour, date=first_saturday + timedelta(weeks=week), defaults={"seats_total": 20}
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Tayyor: {len(CATEGORIES)} toifa, platforma agentligi, {created} ta yangi tur "
                "(rasmlarni admin panel yoki kabinet orqali yuklang)."
            )
        )
