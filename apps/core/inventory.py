"""Platforma boshqaradigan yozuvlarda "bron qilsa bo'ladigan" holatni ta'minlash (har deployda, idempotent).

Excel'dan yuklangan yozuvlarda jo'nash sanalari, xona turlari va gid uchrashuv joylari bo'lmasligi mumkin —
unda ularni hech qaysi kuni bron qilib bo'lmaydi. Bu modul faqat YO'Q narsani qo'shadi, mavjudiga tegmaydi,
va faqat platforma yozuvlariga (`is_platform` / `managed_by_platform`) — hamkorlar o'zi boshqaradi.

- Turlar: keyingi `days` kun ichida haftaning BARCHA kunlari qamralsin — 1 kunlik tur haftada 5 kun,
  2 kunlik — 2 marta, uzun — 1 marta (har bir tur boshqa kunlarda). Mavsum saqlanadi: tur faqat avval
  sanasi bo'lgan oylarda jo'naydi (sanasi umuman yo'q bo'lsa — yil bo'yi).
- Mehmonxonalar: xona turi yo'q bo'lsa — turi va yulduziga mos standart xonalar.
- Gidlar: uchrashuv joyi yo'q bo'lsa — har bir shahrida asosiy diqqatga sazovor joy (yoki shahar markazi).
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

PREMIUM_CITIES = {"toshkent", "samarqand", "buxoro", "xiva"}


def tour_weekdays(duration_days: int, seed: int) -> set[int]:
    if duration_days <= 1:
        return {(seed + k) % 7 for k in (0, 1, 2, 4, 5)}  # haftada 5 kun
    if duration_days == 2:
        return {seed % 7, (seed + 3) % 7}
    return {seed % 7}


def season_months(dates) -> set[int]:
    """Mavsum: birinchi va oxirgi sana orasidagi barcha oylar (dekabr–aprel → 12, 1, 2, 3, 4).
    Sana yo'q yoki ~yil bo'yi bo'lsa — barcha oylar."""
    if not dates:
        return set(range(1, 13))
    first, last = min(dates), max(dates)
    if (last - first).days >= 300:
        return set(range(1, 13))
    months, y, m = set(), first.year, first.month
    while (y, m) <= (last.year, last.month):
        months.add(m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return months


def fill_departures(*, days: int = 120, today=None) -> int:
    from apps.tours.models import Departure, Tour

    today = today or timezone.localdate()
    tours = Tour.objects.filter(status=Tour.Status.PUBLISHED).filter(
        Q(agency__is_platform=True) | Q(agency__managed_by_platform=True)
    )
    created = 0
    for tour in tours.prefetch_related("departures"):
        existing = {d.date for d in tour.departures.all()}
        months = season_months(existing)
        wd = tour_weekdays(tour.duration_days, tour.pk)
        new = [
            Departure(tour=tour, date=d, seats_total=tour.max_group_size)
            for d in (today + timedelta(days=k) for k in range(1, days + 1))
            if d.weekday() in wd and d.month in months and d not in existing
        ]
        Departure.objects.bulk_create(new, ignore_conflicts=True)
        created += len(new)
    return created


def _rooms_for(hotel) -> list[dict]:
    stars = hotel.stars or 3
    base = {3: 350_000, 4: 600_000, 5: 1_200_000}.get(stars, 450_000)
    if hotel.destination.slug not in PREMIUM_CITIES:
        base = int(base * 0.85)
    am = [a for a in hotel.amenities if a in ("wifi", "ac", "breakfast")]

    def r(name, capacity, beds, price, rooms, m2):
        return {
            "name": name,
            "capacity": capacity,
            "beds": beds,
            "price_per_night_uzs": int(round(price, -4)),
            "total_rooms": rooms,
            "size_m2": m2,
            "amenities": am,
        }

    if hotel.kind == "hostel":
        return [
            r("Yotoq joyi (umumiy xona)", 1, "1 yakka karavot", 150_000, 20, None),
            r("Ikki kishilik xona", 2, "1 katta karavot", 380_000, 4, 14),
        ]
    if hotel.kind == "guesthouse":
        return [
            r("Ikki kishilik xona", 2, "1 katta yoki 2 alohida", base * 0.6, 4, 18),
            r("Uch kishilik xona", 3, "1 katta + 1 alohida", base * 0.8, 2, 24),
        ]
    if hotel.kind == "resort":
        return [
            r("Kottej (2 kishilik)", 2, "1 katta karavot", base, 8, 28),
            r("Oilaviy kottej (4 kishilik)", 4, "1 katta + 2 alohida", base * 1.6, 4, 45),
        ]
    rooms = [
        r("Standart (2 kishilik)", 2, "1 katta yoki 2 alohida", base, 12, 22),
        r("Oilaviy (4 kishilik)", 4, "2 katta karavot", base * 1.7, 4, 36),
    ]
    if stars >= 5:
        rooms.append(r("Lyuks", 2, "1 king-size karavot", base * 2.5, 2, 55))
    return rooms


def fill_rooms() -> int:
    from apps.hotels.models import Hotel, RoomType

    created = 0
    for hotel in Hotel.objects.filter(
        managed_by_platform=True, status=Hotel.Status.APPROVED, room_types__isnull=True
    ).select_related("destination"):
        for data in _rooms_for(hotel):
            RoomType.objects.create(hotel=hotel, **data)
            created += 1
    return created


def fill_meeting_points() -> int:
    from apps.catalog.models import Place
    from apps.guides.models import GuideMeetingPoint, GuideProfile

    created = 0
    guides = GuideProfile.objects.filter(
        managed_by_platform=True, status=GuideProfile.Status.APPROVED, meeting_points__isnull=True
    ).prefetch_related("destinations")
    for guide in guides:
        for dest in guide.destinations.all():
            place = (
                Place.objects.filter(destination=dest, is_published=True, latitude__isnull=False)
                .order_by("-is_featured", "pk")
                .first()
            )
            if place is not None:
                name, address, lat, lng = (
                    place.name,
                    place.address or dest.name,
                    place.latitude,
                    place.longitude,
                )
            elif dest.latitude is not None and dest.longitude is not None:
                name, address, lat, lng = (
                    f"{dest.name} markazi",
                    f"{dest.name}, shahar markazi",
                    dest.latitude,
                    dest.longitude,
                )
            else:
                continue
            GuideMeetingPoint.objects.create(
                guide=guide,
                destination=dest,
                name=name[:150],
                address=address[:255],
                latitude=lat,
                longitude=lng,
            )
            created += 1
    return created


def fill_all(*, days: int = 120) -> dict:
    return {
        "departures": fill_departures(days=days),
        "rooms": fill_rooms(),
        "meeting_points": fill_meeting_points(),
    }
