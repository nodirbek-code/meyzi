"""fill_inventory: platforma yozuvlari haftaning barcha kunlarida bron qilinadigan bo'lsin (idempotent)."""

import datetime as dt
from collections import Counter

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.catalog.models import Place
from apps.core.inventory import fill_departures, fill_meeting_points, fill_rooms
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel, RoomType
from apps.tours.models import Departure, Tour

pytestmark = pytest.mark.django_db
TODAY = dt.date(2026, 11, 23)


def make_tour(agency, dest, slug, days=1):
    t = Tour.objects.create(
        agency=agency,
        destination=dest,
        title=slug,
        slug=slug,
        price_uzs=100_000,
        meeting_point="x",
        duration_days=days,
        max_group_size=15,
    )
    Tour.objects.filter(pk=t.pk).update(status=Tour.Status.PUBLISHED)  # /control yoki Excel'dagidek
    t.refresh_from_db()
    return t


@pytest.fixture
def platform(db):
    return Agency.objects.create(name="Demo", slug="demo", managed_by_platform=True)


def test_saturday_only_tours_get_every_weekday(platform, samarqand):
    tours = [make_tour(platform, samarqand, f"t{i}", days=1 + i % 3) for i in range(12)]
    for t in tours:  # eski fayl: faqat shanbalar, dekabr–aprel
        Departure.objects.create(tour=t, date=dt.date(2026, 12, 5), seats_total=15)
        Departure.objects.create(tour=t, date=dt.date(2027, 4, 24), seats_total=15)
    assert fill_departures(days=60, today=TODAY) > 0
    dates = Departure.objects.filter(date__gt=TODAY).values_list("date", flat=True)
    per_weekday = Counter(d.weekday() for d in dates)
    assert set(per_weekday) == set(range(7))  # dushanbadan yakshanbagacha
    window = [TODAY + dt.timedelta(days=k) for k in range(8, 61)]  # dekabr
    assert all(Departure.objects.filter(date=d).exists() for d in window)
    one_day = tours[0]
    assert (
        len({d.weekday() for d in one_day.departures.filter(date__month=12).values_list("date", flat=True)})
        == 5
    )
    assert set(one_day.departures.values_list("seats_total", flat=True)) == {15}
    assert fill_departures(days=60, today=TODAY) == 0  # ikkinchi marta — hech narsa qo'shilmaydi


def test_season_is_kept(platform, samarqand):
    t = make_tour(platform, samarqand, "yozgi")
    Departure.objects.create(tour=t, date=dt.date(2027, 6, 5), seats_total=10)
    fill_departures(days=60, today=TODAY)  # noyabr–yanvar — yozgi tur uchun sana qo'shilmaydi
    assert list(t.departures.values_list("date", flat=True)) == [dt.date(2027, 6, 5)]


def test_partner_tours_untouched(samarqand):
    partner = Agency.objects.create(name="Hamkor", slug="hamkor")
    t = make_tour(partner, samarqand, "hamkor-tur")
    fill_departures(days=30, today=TODAY)
    assert not t.departures.exists()


def test_rooms_for_platform_hotels_only(samarqand):
    def hotel(slug, kind, stars, managed=True, status=Hotel.Status.APPROVED):
        return Hotel.objects.create(
            name=slug,
            slug=slug,
            destination=samarqand,
            address="x",
            phone="+998",
            kind=kind,
            stars=stars,
            amenities=["wifi", "pool"],
            managed_by_platform=managed,
            status=status,
        )

    lux = hotel("lux", "hotel", 5)
    gh = hotel("gh", "guesthouse", 4)
    partner = hotel("partner", "hotel", 4, managed=False)
    has_rooms = hotel("bor", "hotel", 4)
    RoomType.objects.create(hotel=has_rooms, name="Mavjud", capacity=2, price_per_night_uzs=1, total_rooms=1)
    fill_rooms()
    assert [r.name for r in lux.room_types.order_by("pk")] == [
        "Standart (2 kishilik)",
        "Oilaviy (4 kishilik)",
        "Lyuks",
    ]
    assert lux.room_types.first().price_per_night_uzs == 1_200_000 and lux.room_types.first().amenities == [
        "wifi"
    ]
    assert gh.room_types.count() == 2
    assert not partner.room_types.exists() and has_rooms.room_types.count() == 1
    assert fill_rooms() == 0


def test_meeting_points_at_main_place(samarqand, registon):
    u = User.objects.create_user(email="g@g.uz", password="x")
    g = GuideProfile.objects.create(
        user=u,
        slug="g",
        display_name="G",
        phone="+998",
        languages=["uz"],
        price_half_day_uzs=1,
        price_full_day_uzs=1,
        price_per_day_uzs=1,
        status=GuideProfile.Status.APPROVED,
        managed_by_platform=True,
    )
    g.destinations.add(samarqand)
    Place.objects.filter(pk=registon.pk).update(latitude="39.654", longitude="66.975")
    assert fill_meeting_points() == 1
    mp = g.meeting_points.get()
    assert mp.name == registon.name and mp.destination == samarqand
    assert fill_meeting_points() == 0


def test_command_runs(platform, samarqand):
    make_tour(platform, samarqand, "cmd")
    call_command("fill_inventory", "--days", "14")
    assert Departure.objects.filter(tour__slug="cmd").count() >= 9  # 2 hafta × 5 kun (± chegara)
