from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Destination, Place, PlaceCategory

# Demo ma'lumotlar. Koordinatalar taxminiy, kirish narxlari namunaviy —
# real narxlarni admin panel orqali yangilang.
DESTINATIONS = [
    {
        "slug": "toshkent",
        "name": "Toshkent",
        "region": "Toshkent shahri",
        "sort_order": 1,
        "latitude": "41.311081",
        "longitude": "69.240562",
        "short_description": "Poytaxt: zamonaviy shahar va qadimiy Eski shahar.",
        "places": [
            ("hazrati-imom", "Hazrati Imom majmuasi", PlaceCategory.MOSQUE, "41.338300", "69.240900", 0),
            ("chorsu-bozori", "Chorsu bozori", PlaceCategory.BAZAAR, "41.326400", "69.236400", 0),
            (
                "temuriylar-tarixi-muzeyi",
                "Temuriylar tarixi davlat muzeyi",
                PlaceCategory.MUSEUM,
                "41.311900",
                "69.279600",
                30000,
            ),
        ],
    },
    {
        "slug": "samarqand",
        "name": "Samarqand",
        "region": "Samarqand viloyati",
        "sort_order": 2,
        "latitude": "39.654167",
        "longitude": "66.959722",
        "is_featured": True,
        "short_description": "Ipak yo'lining durdonasi — Registon, Shohi Zinda, Bibixonim.",
        "places": [
            ("registon", "Registon maydoni", PlaceCategory.MONUMENT, "39.654800", "66.975800", 65000),
            ("shohi-zinda", "Shohi Zinda majmuasi", PlaceCategory.MONUMENT, "39.662800", "66.987600", 40000),
            ("bibixonim-masjidi", "Bibixonim masjidi", PlaceCategory.MOSQUE, "39.660900", "66.979300", 40000),
            ("siyob-bozori", "Siyob bozori", PlaceCategory.BAZAAR, "39.661500", "66.981000", 0),
        ],
    },
    {
        "slug": "buxoro",
        "name": "Buxoro",
        "region": "Buxoro viloyati",
        "sort_order": 3,
        "latitude": "39.767500",
        "longitude": "64.423100",
        "is_featured": True,
        "short_description": "2500 yillik muzey-shahar.",
        "places": [
            ("ark-qalasi", "Ark qal'asi", PlaceCategory.MONUMENT, "39.777900", "64.410900", 40000),
            ("poi-kalon", "Poi Kalon majmuasi", PlaceCategory.MOSQUE, "39.775800", "64.414800", 20000),
            ("labi-hovuz", "Labi Hovuz", PlaceCategory.MONUMENT, "39.773700", "64.420800", 0),
        ],
    },
    {
        "slug": "xiva",
        "name": "Xiva",
        "region": "Xorazm viloyati",
        "sort_order": 4,
        "latitude": "41.378300",
        "longitude": "60.363900",
        "is_featured": True,
        "short_description": "Ochiq osmon ostidagi muzey — Ichan Qal'a.",
        "places": [
            ("ichan-qala", "Ichan Qal'a", PlaceCategory.MONUMENT, "41.378000", "60.359500", 150000),
            ("kalta-minor", "Kalta Minor", PlaceCategory.MONUMENT, "41.378300", "60.358600", 0),
        ],
    },
]


class Command(BaseCommand):
    help = "Katalogga demo shaharlar va joylarni yuklaydi (qayta ishga tushirish xavfsiz)."

    @transaction.atomic
    def handle(self, *args, **options):
        d_count = p_count = 0
        for data in DESTINATIONS:
            data = dict(data)
            places = data.pop("places")
            slug = data.pop("slug")
            destination, created = Destination.objects.update_or_create(slug=slug, defaults=data)
            d_count += created
            for p_slug, name, category, lat, lng, fee in places:
                _, created = Place.objects.update_or_create(
                    slug=p_slug,
                    defaults={
                        "destination": destination,
                        "name": name,
                        "category": category,
                        "latitude": lat,
                        "longitude": lng,
                        "entry_fee_uzs": fee,
                    },
                )
                p_count += created
        self.stdout.write(self.style.SUCCESS(f"Tayyor: {d_count} ta yangi shahar, {p_count} ta yangi joy."))
