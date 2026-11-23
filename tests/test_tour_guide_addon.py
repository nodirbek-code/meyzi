"""Ixtiyoriy professional gid: yo'lboshchi doim narxda, gid — guruh uchun bir marta, turist tanlaydi."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.bookings import services
from apps.bookings.models import Booking
from apps.guides.models import GuideProfile, GuideUnavailableDate
from apps.guides.services import busy_dates
from apps.tours.models import Departure

pytestmark = pytest.mark.django_db
T = "/api/v1/tours/"


def make_guide(slug, langs=("uz", "en"), status=GuideProfile.Status.APPROVED):
    u = User.objects.create_user(email=f"{slug}@g.uz", password="x")
    return GuideProfile.objects.create(
        user=u,
        slug=slug,
        display_name=slug.title(),
        phone="+998900000001",
        languages=list(langs),
        price_half_day_uzs=1,
        price_full_day_uzs=1,
        price_per_day_uzs=1,
        status=status,
    )


@pytest.fixture
def setup(tour, departure):
    tour.guide_price_uzs = 300_000
    tour.save(update_fields=["guide_price_uzs"])
    g = make_guide("jasur")
    tour.guides.add(g)
    return tour, departure, g


def book(user, departure, guide=None, seats=2, **kw):
    return services.create_booking(
        user=user,
        departure_id=departure.pk,
        seats=seats,
        contact_name="Ali",
        contact_phone="+998901234567",
        guide=guide,
        **kw,
    )


def test_without_guide_price_is_per_person_only(user, setup):
    tour, dep, _ = setup
    b = book(user, dep)
    assert b.guide is None and b.guide_price_uzs == 0 and b.total_uzs == tour.price_uzs * 2


def test_guide_added_once_per_group(user, setup):
    tour, dep, g = setup
    b = book(user, dep, guide="jasur", seats=3)
    assert b.guide == g and b.guide_price_uzs == 300_000
    assert b.total_uzs == tour.price_uzs * 3 + 300_000  # guruh uchun bir marta, kishi boshiga emas
    assert b.agency_amount_uzs + b.commission_uzs == b.total_uzs


def test_same_guide_cannot_be_taken_twice_on_same_day(user, setup, db):
    tour, dep, g = setup
    book(user, dep, guide="jasur")
    other = User.objects.create_user(email="o@x.uz", password="x")
    with pytest.raises(ValidationError) as e:
        book(other, dep, guide="jasur")
    assert "band" in str(e.value.detail["guide"])
    later = Departure.objects.create(tour=tour, date=dep.date + timedelta(days=1), seats_total=10)
    assert book(other, later, guide="jasur").guide == g  # boshqa kun — bo'sh


def test_multi_day_tour_blocks_every_day(user, setup):
    tour, dep, g = setup
    tour.duration_days = 3
    tour.save(update_fields=["duration_days"])
    book(user, dep, guide="jasur")
    assert busy_dates(g, start=dep.date, end=dep.date + timedelta(days=5)) == {
        dep.date,
        dep.date + timedelta(days=1),
        dep.date + timedelta(days=2),
    }
    clash = Departure.objects.create(tour=tour, date=dep.date + timedelta(days=2), seats_total=10)
    with pytest.raises(ValidationError):
        book(User.objects.create_user(email="z@x.uz", password="x"), clash, guide="jasur")


def test_expired_unpaid_booking_frees_guide(user, setup):
    _, dep, g = setup
    b = book(user, dep, guide="jasur")
    Booking.objects.filter(pk=b.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
    assert busy_dates(g, start=dep.date, end=dep.date) == set()


def test_guide_own_day_off_blocks(user, setup):
    _, dep, g = setup
    GuideUnavailableDate.objects.create(guide=g, date=dep.date)
    with pytest.raises(ValidationError):
        book(user, dep, guide="jasur")


@pytest.mark.parametrize("case", ["not_attached", "no_service", "pending"])
def test_invalid_guide_choices(user, setup, case):
    tour, dep, _ = setup
    slug = "jasur"
    if case == "not_attached":
        make_guide("begona")
        slug = "begona"
    elif case == "no_service":
        tour.guide_price_uzs = None
        tour.save(update_fields=["guide_price_uzs"])
    else:
        tour.guides.add(make_guide("yangi", status=GuideProfile.Status.PENDING))
        slug = "yangi"
    with pytest.raises(ValidationError):
        book(user, dep, guide=slug)
    assert not Booking.objects.exists()


def test_guides_endpoint_shows_availability(api, user, setup):
    tour, dep, _ = setup
    tour.guides.add(make_guide("olga", ("ru", "en")))
    book(user, dep, guide="jasur")
    data = api.get(T + f"{tour.slug}/guides/", {"departure": dep.pk}).data
    assert {g["slug"]: g["available"] for g in data} == {"jasur": False, "olga": True}
    assert "phone" not in data[0]
    assert api.get(T + f"{tour.slug}/").data["guide_price_uzs"] == 300_000
    assert api.get(T + f"{tour.slug}/guides/").status_code == 400


def test_guide_phone_only_after_confirmation(auth_api, user, setup):
    _, dep, _ = setup
    b = book(user, dep, guide="jasur")
    data = auth_api.get(f"/api/v1/bookings/{b.code}/").data
    assert data["guide"]["display_name"] == "Jasur" and data["guide"]["phone"] is None
    services.confirm_booking(b)
    assert auth_api.get(f"/api/v1/bookings/{b.code}/").data["guide"]["phone"] == "+998900000001"


def test_booking_api_accepts_guide(auth_api, user, setup):
    _, dep, _ = setup
    user.phone, user.phone_verified = "+998901234567", True
    user.save(update_fields=["phone", "phone_verified"])
    r = auth_api.post(
        "/api/v1/bookings/",
        {
            "departure": dep.pk,
            "seats": 1,
            "contact_name": "Ali",
            "contact_phone": "+998901234567",
            "guide": "jasur",
        },
        format="json",
    )
    assert r.status_code == 201, r.data
    assert r.data["guide_price_uzs"] == 300_000 and r.data["guide"]["slug"] == "jasur"


def test_guide_sees_tour_jobs_in_cabinet(user, setup):
    from rest_framework.test import APIClient

    _, dep, g = setup
    b = book(user, dep, guide="jasur")
    c = APIClient()
    c.force_authenticate(g.user)
    jobs = c.get("/api/v1/cabinet/guide/tour-bookings/").data
    assert [j["code"] for j in jobs] == [b.code] and jobs[0]["contact_phone"] is None  # to'lovgacha yashirin
    services.confirm_booking(b)
    assert c.get("/api/v1/cabinet/guide/tour-bookings/").data[0]["contact_phone"] == "+998901234567"
