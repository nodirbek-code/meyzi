from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from apps.agencies.models import Agency
from apps.tours.models import Departure, Tour, TourCategory, TourMedia
from apps.tours.policies import refund_ratio
from apps.tours.pricing import installment

from .media_samples import PNG

pytestmark = pytest.mark.django_db

# 1x1 PNG


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


# ---------- Narx va siyosat ----------


@pytest.mark.parametrize(("price", "monthly"), [(890_000, 106_800), (170_000, 20_400)])
def test_installment_matches_triphub(price, monthly):
    assert installment(price) == {"months": 12, "monthly_uzs": monthly, "total_uzs": monthly * 12}


@pytest.mark.parametrize(
    ("policy", "hours_left", "ratio"),
    [
        ("free", 24, "1"),
        ("free", 23.9, "0"),
        ("partial", 48.1, "0.5"),
        ("partial", 48, "0"),
        ("non_refundable", 500, "0"),
    ],
)
def test_refund_ratio(policy, hours_left, ratio):
    dep = datetime(2027, 1, 10, 8, 0)
    assert refund_ratio(policy, dep, dep - timedelta(hours=hours_left)) == Decimal(ratio)


# ---------- Ommaviy katalog ----------


def test_tour_list_card(api, tour, departure):
    res = api.get("/api/v1/tours/")
    assert res.status_code == 200
    card = res.data["results"][0]
    assert card["slug"] == "samarqand-1-kun"
    assert card["installment"]["monthly_uzs"] == 106_800
    assert card["next_departure"]["date"] == str(departure.date)
    assert card["next_departure"]["seats_left"] == 20
    assert card["agency"]["slug"] == "vodiy-tour"
    assert card["categories"] == [{"name": "Tog'", "slug": "tog"}]


def test_only_published_tours_visible(api, tour, agency):
    Tour.objects.create(agency=agency, destination=tour.destination, title="Q", slug="qoralama", price_uzs=1)
    assert api.get("/api/v1/tours/").data["count"] == 1
    assert api.get("/api/v1/tours/qoralama/").status_code == 404

    agency.status = Agency.Status.SUSPENDED
    agency.save()
    assert api.get("/api/v1/tours/").data["count"] == 0


def test_tour_detail(api, tour, departure):
    past = Departure.objects.create(tour=tour, date=timezone.localdate() - timedelta(days=1), seats_total=5)
    res = api.get(f"/api/v1/tours/{tour.slug}/")
    assert res.status_code == 200
    assert [d["id"] for d in res.data["departures"]] == [departure.id]
    assert past.id not in [d["id"] for d in res.data["departures"]]
    assert "24 soat" in res.data["cancellation_policy_text"]


def test_next_departure_skips_sold_out(api, tour, departure):
    departure.seats_booked = 20
    departure.save()
    later = Departure.objects.create(tour=tour, date=departure.date + timedelta(days=7), seats_total=10)
    card = api.get("/api/v1/tours/").data["results"][0]
    assert card["next_departure"]["id"] == later.id


def test_tour_filters(api, tour, departure, agency, category):
    from apps.catalog.models import Destination
    from apps.tours.models import TourCategory

    buxoro = Destination.objects.create(name="Buxoro", slug="buxoro")
    madaniy = TourCategory.objects.create(name="Madaniy", slug="madaniy")
    other = Tour.objects.create(
        agency=agency,
        destination=buxoro,
        title="Buxoro 3 kun",
        slug="buxoro-3",
        price_uzs=2_000_000,
        duration_days=3,
    )
    other.categories.add(madaniy)
    other.publish()
    other.save()

    def slugs(q):
        return {t["slug"] for t in api.get(f"/api/v1/tours/{q}").data["results"]}

    assert slugs("?destination=buxoro") == {"buxoro-3"}
    assert slugs("?category=tog") == {"samarqand-1-kun"}
    assert slugs("?category=tog,madaniy") == {"samarqand-1-kun", "buxoro-3"}
    assert slugs("?max_price=1000000") == {"samarqand-1-kun"}
    assert slugs("?min_days=2") == {"buxoro-3"}
    assert slugs(f"?date={departure.date}") == {"samarqand-1-kun"}
    assert slugs(f"?date_from={departure.date + timedelta(days=1)}") == set()
    assert slugs("?search=buxoro") == {"buxoro-3"}

    ordered = [t["slug"] for t in api.get("/api/v1/tours/?ordering=-price_uzs").data["results"]]
    assert ordered == ["buxoro-3", "samarqand-1-kun"]


def test_categories_count_only_public(api, tour, category):
    counts = {c["slug"]: c["tours_count"] for c in api.get("/api/v1/tours/categories/").data}
    assert counts[category.slug] == 1
    assert counts["tarix"] == 0  # boshqa toifalar ham ro'yxatda, turi yo'q


# ---------- Agentlik kabineti ----------

TOUR_PAYLOAD = {
    "title": "Zomin 2 kun",
    "destination": "samarqand",
    "categories": ["tog"],
    "duration_days": 2,
    "duration_nights": 1,
    "price_uzs": 890000,
    "cancellation_policy": "free",
    "meeting_point": "Toshkent, Amir Temur xiyoboni",
    "meeting_map_url": "https://yandex.uz/maps/?pt=69.279737,41.311151&z=16",
    "included": ["Transport", "Gid"],
    "itinerary": [
        {
            "day_number": 1,
            "title": "Yo'l",
            "items": [{"start_time": "06:00", "end_time": "06:30", "title": "Yig'ilish"}],
        },
        {"day_number": 2, "items": [{"title": "Qaytish"}]},
    ],
}


def test_cabinet_requires_agency(auth_api, api):
    assert api.get("/api/v1/cabinet/tours/").status_code == 401
    assert auth_api.get("/api/v1/cabinet/tours/").status_code == 403


def test_cabinet_create_tour_with_itinerary(agency_api, agency, samarqand, category):
    res = agency_api.post("/api/v1/cabinet/tours/", TOUR_PAYLOAD, format="json")
    assert res.status_code == 201, res.data
    assert res.data["status"] == "draft"
    assert res.data["slug"] == "zomin-2-kun"
    tour = Tour.objects.get(slug="zomin-2-kun")
    assert tour.agency == agency
    assert tour.itinerary.count() == 2
    assert tour.itinerary.get(day_number=1).items.get().title == "Yig'ilish"

    # dasturni almashtirish
    res = agency_api.patch(
        f"/api/v1/cabinet/tours/{tour.slug}/", {"itinerary": [{"day_number": 1, "items": []}]}, format="json"
    )
    assert res.status_code == 200
    assert tour.itinerary.count() == 1


def test_cabinet_itinerary_day_out_of_range(agency_api, samarqand, category):
    payload = {**TOUR_PAYLOAD, "itinerary": [{"day_number": 3}]}
    res = agency_api.post("/api/v1/cabinet/tours/", payload, format="json")
    assert res.status_code == 400
    assert "itinerary" in res.data


def test_cabinet_cannot_touch_other_agency_tour(agency_api, samarqand, category):
    other = Agency.objects.create(name="Boshqa", slug="boshqa")
    t = Tour.objects.create(agency=other, destination=samarqand, title="B", slug="begona", price_uzs=1)
    assert agency_api.get("/api/v1/cabinet/tours/begona/").status_code == 404
    assert (
        agency_api.patch("/api/v1/cabinet/tours/begona/", {"price_uzs": 5}, format="json").status_code == 404
    )
    assert agency_api.get(f"/api/v1/cabinet/tours/{t.slug}/departures/").status_code == 404


def test_submit_flow_moderation_and_auto_publish(agency_api, agency, samarqand, category):
    slug = agency_api.post("/api/v1/cabinet/tours/", TOUR_PAYLOAD, format="json").data["slug"]

    # rasm yo'q — yuborib bo'lmaydi
    assert agency_api.post(f"/api/v1/cabinet/tours/{slug}/submit/").status_code == 400

    img = SimpleUploadedFile("a.png", PNG, content_type="image/png")
    res = agency_api.post(
        f"/api/v1/cabinet/tours/{slug}/media/", {"file": img, "is_cover": True}, format="multipart"
    )
    assert res.status_code == 201, res.data

    res = agency_api.post(f"/api/v1/cabinet/tours/{slug}/submit/")
    assert res.data["status"] == "pending_review"

    # oddiy agentlikda auto_publish yoqilgan bo'lsa ham — baribir admin tekshiruvi
    agency.auto_publish = True
    agency.save()
    Tour.objects.filter(slug=slug).update(status=Tour.Status.DRAFT)
    res = agency_api.post(f"/api/v1/cabinet/tours/{slug}/submit/")
    assert res.data["status"] == "pending_review"

    # faqat platformaning o'z agentligi (MEYZI) — darhol e'lon
    agency.is_platform = True
    agency.save()
    Tour.objects.filter(slug=slug).update(status=Tour.Status.DRAFT)
    res = agency_api.post(f"/api/v1/cabinet/tours/{slug}/submit/")
    assert res.data["status"] == "published"
    assert res.data["published_at"]


def test_single_cover(agency_api, tour, agency_user):
    url = f"/api/v1/cabinet/tours/{tour.slug}/media/"
    a = agency_api.post(url, {"file": SimpleUploadedFile("a.png", PNG), "is_cover": True}, format="multipart")
    b = agency_api.post(url, {"file": SimpleUploadedFile("b.png", PNG), "is_cover": True}, format="multipart")
    assert TourMedia.objects.get(pk=a.data["id"]).is_cover is False
    assert TourMedia.objects.get(pk=b.data["id"]).is_cover is True


def test_cabinet_departures(agency_api, tour):
    url = f"/api/v1/cabinet/tours/{tour.slug}/departures/"
    day = timezone.localdate() + timedelta(days=10)

    res = agency_api.post(url, {"date": str(day), "seats_total": 15}, format="json")
    assert res.status_code == 201, res.data
    dep_id = res.data["id"]

    assert agency_api.post(url, {"date": str(day), "seats_total": 5}, format="json").status_code == 400
    past = timezone.localdate() - timedelta(days=1)
    assert agency_api.post(url, {"date": str(past), "seats_total": 5}, format="json").status_code == 400

    Departure.objects.filter(pk=dep_id).update(seats_booked=10)
    res = agency_api.patch(f"{url}{dep_id}/", {"seats_total": 5}, format="json")
    assert res.status_code == 400
    # bronli sanani o'chirish taqiqi — tests/test_bookings.py::test_cancelling_departure_cancels_bookings


def test_cabinet_stats(agency_api, tour, departure):
    res = agency_api.get("/api/v1/cabinet/stats/")
    assert res.status_code == 200
    assert res.data["tours_total"] == 1
    assert res.data["tours_by_status"]["published"] == 1
    assert res.data["upcoming_seats_total"] == 20


def test_seed_tours_idempotent(api):
    call_command("seed_tours")
    call_command("seed_tours")
    assert Tour.objects.filter(agency__slug="meyzi", status=Tour.Status.PUBLISHED).count() == 3
    meyzi = Agency.objects.get(slug="meyzi")
    assert meyzi.is_platform and meyzi.auto_publish and meyzi.commission_percent == 0
    assert api.get("/api/v1/tours/?category=tog").data["count"] == 2
    # Toifalar yagona ro'yxatdan: eski "madaniy" / "dam-olish-kuni" qaytib kelmaydi
    from apps.tours.categories import CATEGORIES

    assert list(TourCategory.objects.order_by("sort_order").values_list("slug", flat=True)) == [
        c[0] for c in CATEGORIES
    ]
    assert api.get("/api/v1/tours/?category=qisqa-sayohat").data["count"] == 1


def test_calendar_counts_open_departures(api, tour, departure):
    res = api.get("/api/v1/tours/calendar/", {"days": 30})
    assert res.status_code == 200
    assert res.data == [{"date": departure.date.isoformat(), "tours": 1}]
    assert api.get("/api/v1/tours/calendar/", {"destination": "yoq"}).data == []
