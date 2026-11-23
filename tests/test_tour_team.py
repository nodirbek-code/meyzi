"""Tur jamoasi: turga gid va mehmonxona biriktirish, filtrlar va Excel'dan dastur/sanalar bilan import."""

import datetime as dt
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel
from apps.tours.models import Tour, TourCategory

pytestmark = pytest.mark.django_db
T = "/api/v1/tours/"
M = "/api/v1/control/manage/"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def make_guide(slug, langs, status=GuideProfile.Status.APPROVED):
    u = User.objects.create_user(email=f"{slug}@g.uz", password="x")
    return GuideProfile.objects.create(
        user=u,
        slug=slug,
        display_name=slug.title(),
        phone="+998901110000",
        languages=langs,
        price_half_day_uzs=1,
        price_full_day_uzs=1,
        price_per_day_uzs=1,
        status=status,
    )


def make_hotel(slug, dest, status=Hotel.Status.APPROVED):
    return Hotel.objects.create(
        name=slug.title(), slug=slug, destination=dest, address="x", phone="+998", stars=4, status=status
    )


@pytest.fixture
def team(tour, samarqand):
    ja = make_guide("kenji", ["uz", "ja"])
    ru = make_guide("olga", ["ru", "en"])
    hidden = make_guide("yangi", ["ja"], status=GuideProfile.Status.PENDING)
    h = make_hotel("registan-palace", samarqand)
    h_hidden = make_hotel("yopiq", samarqand, status=Hotel.Status.PENDING)
    tour.guides.set([ja, hidden])
    tour.hotels.set([h, h_hidden])
    return {"ja": ja, "ru": ru, "hidden": hidden, "hotel": h, "hotel_hidden": h_hidden}


def slugs(res):
    return [t["slug"] for t in res.data["results"]]


def test_detail_shows_only_approved_team_without_contacts(api, tour, team):
    data = api.get(T + f"{tour.slug}/").data
    assert [g["slug"] for g in data["guides"]] == ["kenji"]
    assert "phone" not in data["guides"][0]  # gid telefoni faqat gid bronidan keyin
    assert data["guides"][0]["languages"] == ["uz", "ja"]
    assert [h["slug"] for h in data["hotels"]] == ["registan-palace"]
    assert data["hotels"][0]["destination"] == "Samarqand" and data["hotels"][0]["stars"] == 4


def test_filter_by_guide_hotel_and_language(api, tour, team):
    assert slugs(api.get(T, {"guide": "kenji"})) == [tour.slug]
    assert slugs(api.get(T, {"guide": "olga"})) == []
    assert slugs(api.get(T, {"guide": "yangi"})) == []  # tasdiqlanmagan gid bo'yicha topilmaydi
    assert slugs(api.get(T, {"hotel": "registan-palace"})) == [tour.slug]
    assert slugs(api.get(T, {"hotel": "yopiq"})) == []
    assert slugs(api.get(T, {"language": "ja"})) == [tour.slug]
    assert slugs(api.get(T, {"language": "JA"})) == [tour.slug]
    assert slugs(api.get(T, {"language": "ru"})) == []
    assert slugs(api.get(T, {"language": "j"})) == []  # "ja" ichidagi qism emas — to'liq kod
    assert slugs(api.get(T, {"language": '"%'})) == []


def test_language_filter_no_duplicates(api, tour, team):
    tour.guides.add(make_guide("aiko", ["ja"]))
    assert slugs(api.get(T, {"language": "ja"})) == [tour.slug]


# ---------- Excel import ----------


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def xlsx(header, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile("t.xlsx", buf.getvalue(), content_type=XLSX)


HEAD = [
    "Agentlik",
    "Yo'nalish",
    "Nomi",
    "Toifalar",
    "Kunlar",
    "Guruhdagi maks. odam",
    "Uchrashuv joyi",
    "Narx (so'm, 1 kishi)",
    "Gidlar",
    "Mehmonxonalar",
    "Kunlik dastur",
    "Jo'nash sanalari",
]


@pytest.fixture
def base(samarqand):
    Agency.objects.create(name="MEYZI", slug="meyzi", is_platform=True)
    TourCategory.objects.create(name="Madaniy", slug="madaniy")
    return {
        "guide": make_guide("jasur", ["uz", "en"]),
        "hotel": make_hotel("afrosiyob", samarqand),
    }


def future(days):
    return (timezone.localdate() + dt.timedelta(days=days)).isoformat()


def test_import_tour_with_team_itinerary_and_departures(staff_api, base):
    row = [
        "MEYZI",
        "Samarqand",
        "Samarqand 2 kun",
        "Madaniy",
        2,
        12,
        "Registon",
        "1 200 000",
        "Jasur",
        "Afrosiyob",
        "Registon va Shohi Zinda: madrasalar, maqbaralar\nAfrosiyob: muzey va qog'oz ustaxonasi",
        f"{future(10)}, {future(24)}, {future(10)}",
    ]
    r = staff_api.post(M + "tour/import/", {"file": xlsx(HEAD, [row])}, format="multipart")
    assert r.status_code == 201, r.data
    t = Tour.objects.get(title="Samarqand 2 kun")
    assert list(t.guides.all()) == [base["guide"]] and list(t.hotels.all()) == [base["hotel"]]
    days = list(t.itinerary.order_by("day_number").values_list("day_number", "title", "description"))
    assert days == [
        (1, "Registon va Shohi Zinda", "madrasalar, maqbaralar"),
        (2, "Afrosiyob", "muzey va qog'oz ustaxonasi"),
    ]
    deps = list(t.departures.order_by("date").values_list("date", "seats_total"))
    assert [(d.isoformat(), s) for d, s in deps] == [
        (future(10), 12),
        (future(24), 12),
    ]  # takror olib tashlandi


@pytest.mark.parametrize(
    ("itinerary", "departures", "message"),
    [
        ("1-kun: a\n2-kun: b\n3-kun: c", "", "Dasturda 3 kun"),
        ("", "2020-01-01", "O'tgan sana"),
        ("", "31.12.2026", "YYYY-MM-DD"),
    ],
)
def test_import_tour_extras_errors_roll_back(staff_api, base, itinerary, departures, message):
    row = [
        "MEYZI",
        "Samarqand",
        "Xato tur",
        "Madaniy",
        2,
        10,
        "Registon",
        100000,
        "",
        "",
        itinerary,
        departures,
    ]
    r = staff_api.post(M + "tour/import/", {"file": xlsx(HEAD, [row])}, format="multipart")
    assert r.status_code == 400
    assert message in " ".join(r.data["rows"][0]["errors"])
    assert not Tour.objects.filter(title="Xato tur").exists()


def test_unapproved_guide_cannot_be_attached(staff_api, base):
    make_guide("kutilmoqda", ["uz"], status=GuideProfile.Status.PENDING)
    row = ["MEYZI", "Samarqand", "Tur", "Madaniy", 1, 10, "Registon", 100000, "Kutilmoqda", "", "", ""]
    r = staff_api.post(M + "tour/import/", {"file": xlsx(HEAD, [row])}, format="multipart")
    assert r.status_code == 400 and "topilmadi" in " ".join(r.data["rows"][0]["errors"])
