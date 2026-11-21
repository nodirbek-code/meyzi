from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.catalog.models import Destination
from apps.guides.models import GuideMeetingPoint, GuideProfile
from apps.hotels.models import Hotel, RoomType

GUIDES = [
    {
        "email": "demo.gid.aziz@lazuri.local",
        "slug": "aziz-karimov",
        "display_name": "Aziz Karimov",
        "bio": "Samarqand tarixi bo'yicha 8 yillik tajribali gid.",
        "languages": ["uz", "ru", "en"],
        "specializations": ["history", "city"],
        "destinations": ["samarqand", "buxoro"],
        "experience_years": 8,
        "prices": (300_000, 500_000, 450_000),
    },
    {
        "email": "demo.gid.dilnoza@lazuri.local",
        "slug": "dilnoza-rahimova",
        "display_name": "Dilnoza Rahimova",
        "bio": "Tog' sayohatlari va milliy taomlar bo'yicha gid.",
        "languages": ["uz", "en", "de"],
        "specializations": ["mountain", "food", "nature"],
        "destinations": ["toshkent", "chimyon", "zomin"],
        "experience_years": 5,
        "prices": (250_000, 400_000, 380_000),
    },
]

HOTELS = [
    {
        "slug": "demo-registon-hotel",
        "name": "Demo Registon Hotel",
        "destination": "samarqand",
        "stars": 4,
        "address": "Samarqand, Registon ko'chasi",
        "amenities": ["wifi", "breakfast", "ac", "parking"],
        "rooms": [("Standart ikki kishilik", 2, 600_000, 10), ("Oilaviy", 4, 950_000, 4)],
    },
    {
        "slug": "demo-buxoro-guesthouse",
        "name": "Demo Buxoro Guest House",
        "destination": "buxoro",
        "stars": 3,
        "kind": "guesthouse",
        "address": "Buxoro, Labi Hovuz yaqinida",
        "amenities": ["wifi", "breakfast"],
        "rooms": [("Ikki kishilik", 2, 400_000, 6)],
    },
]


class Command(BaseCommand):
    help = "To'liq demo: turlar, FAQ, 2 gid, 2 mehmonxona. Qayta ishga tushirish xavfsiz."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_tours")
        call_command("seed_content")

        for g in GUIDES:
            user, created = User.objects.get_or_create(
                email=g["email"],
                defaults={"first_name": g["display_name"].split()[0], "role": User.Role.GUIDE},
            )
            if created:
                user.set_unusable_password()  # demo akkauntga kirib bo'lmaydi
                user.save()
            half, full, per_day = g["prices"]
            profile, _ = GuideProfile.objects.update_or_create(
                slug=g["slug"],
                defaults={
                    "user": user,
                    "display_name": g["display_name"],
                    "bio": g["bio"],
                    "phone": "+998900000000",
                    "languages": g["languages"],
                    "specializations": g["specializations"],
                    "experience_years": g["experience_years"],
                    "price_half_day_uzs": half,
                    "price_full_day_uzs": full,
                    "price_per_day_uzs": per_day,
                    "status": GuideProfile.Status.APPROVED,
                    "is_certified": True,
                },
            )
            profile.destinations.set(Destination.objects.filter(slug__in=g["destinations"]))
            for dest in profile.destinations.exclude(latitude=None).exclude(longitude=None):
                GuideMeetingPoint.objects.get_or_create(
                    guide=profile,
                    destination=dest,
                    name=f"{dest.name} markazi",
                    defaults={"address": dest.name, "latitude": dest.latitude, "longitude": dest.longitude},
                )

        for h in HOTELS:
            hotel, _ = Hotel.objects.update_or_create(
                slug=h["slug"],
                defaults={
                    "name": h["name"],
                    "kind": h.get("kind", Hotel.Kind.HOTEL),
                    "destination": Destination.objects.get(slug=h["destination"]),
                    "stars": h["stars"],
                    "address": h["address"],
                    "phone": "+998660000000",
                    "amenities": h["amenities"],
                    "status": Hotel.Status.APPROVED,
                },
            )
            for name, capacity, price, total in h["rooms"]:
                RoomType.objects.update_or_create(
                    hotel=hotel,
                    name=name,
                    defaults={"capacity": capacity, "price_per_night_uzs": price, "total_rooms": total},
                )

        self.stdout.write(self.style.SUCCESS(f"Demo: {len(GUIDES)} gid, {len(HOTELS)} mehmonxona."))
