from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.bookings import services as booking_services
from apps.bookings.models import Booking
from apps.reviews import services
from apps.reviews.models import Review

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed(departure):
    """Yakunlangan bron yaratuvchi."""

    def _make(user):
        b = booking_services.create_booking(
            user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="+998900000000"
        )
        Booking.objects.filter(pk=b.pk).update(status=Booking.Status.COMPLETED, expires_at=None)
        b.refresh_from_db()
        return b

    return _make


def test_review_flow_and_ratings(auth_api, user, completed, tour, agency):
    booking = completed(user)
    res = auth_api.post(
        "/api/v1/reviews/my/", {"booking": booking.code, "rating": 5, "text": "Zo'r!"}, format="json"
    )
    assert res.status_code == 201, res.data

    other = User.objects.create_user(
        email="o@example.com", password=PASSWORD, first_name="Vali", last_name="Karimov"
    )
    services.create_review(user=other, booking_code=completed(other).code, rating=4)

    # tekshiruvda — saytda ham, reytingda ham yo'q
    tour.refresh_from_db()
    assert (tour.rating, tour.reviews_count) == (Decimal("0.00"), 0)
    assert APIClient().get(f"/api/v1/reviews/?tour={tour.slug}").data["results"] == []
    for r in Review.objects.all():
        services.set_status(r, Review.Status.PUBLISHED)  # admin tasdiqladi

    tour.refresh_from_db()
    agency.refresh_from_db()
    assert (tour.rating, tour.reviews_count) == (Decimal("4.50"), 2)
    assert (agency.rating, agency.reviews_count) == (Decimal("4.50"), 2)

    public = APIClient().get(f"/api/v1/reviews/?tour={tour.slug}").data["results"]
    assert {r["author"] for r in public} == {"Ali", "Vali K."}  # familiya to'liq ko'rinmaydi
    assert "user" not in public[0]


def test_only_completed_booking(auth_api, user, departure):
    b = booking_services.create_booking(
        user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="+998900000000"
    )
    res = auth_api.post("/api/v1/reviews/my/", {"booking": b.code, "rating": 5}, format="json")
    assert res.status_code == 400


def test_one_review_per_booking(user, completed):
    b = completed(user)
    services.create_review(user=user, booking_code=b.code, rating=5)
    with pytest.raises(ValidationError):
        services.create_review(user=user, booking_code=b.code, rating=3)


def test_cannot_review_others_booking(auth_api, completed):
    other = User.objects.create_user(email="o@example.com", password=PASSWORD)
    b = completed(other)
    res = auth_api.post("/api/v1/reviews/my/", {"booking": b.code, "rating": 5}, format="json")
    assert res.status_code == 400


def test_rating_bounds(auth_api, user, completed):
    b = completed(user)
    for bad in (0, 6):
        assert (
            auth_api.post(
                "/api/v1/reviews/my/", {"booking": b.code, "rating": bad}, format="json"
            ).status_code
            == 400
        )


def test_edit_window(auth_api, user, completed, tour):
    review = services.create_review(user=user, booking_code=completed(user).code, rating=2)
    services.set_status(review, Review.Status.PUBLISHED)
    res = auth_api.patch(f"/api/v1/reviews/my/{review.id}/", {"rating": 4}, format="json")
    assert res.status_code == 200
    review.refresh_from_db()
    assert review.status == Review.Status.PENDING  # o'zgartirilgan sharh qayta tekshiruvga
    services.set_status(review, Review.Status.PUBLISHED)
    tour.refresh_from_db()
    assert tour.rating == Decimal("4.00")

    Review.objects.filter(pk=review.pk).update(created_at=timezone.now() - timedelta(days=15))
    assert auth_api.patch(f"/api/v1/reviews/my/{review.id}/", {"rating": 5}, format="json").status_code == 400


def test_hidden_review_excluded(api, user, completed, tour):
    review = services.create_review(user=user, booking_code=completed(user).code, rating=1)
    services.set_status(review, Review.Status.HIDDEN)
    tour.refresh_from_db()
    assert (tour.rating, tour.reviews_count) == (Decimal("0.00"), 0)
    assert api.get("/api/v1/reviews/").data["count"] == 0


def test_agency_reply(agency_api, user, completed):
    review = services.create_review(user=user, booking_code=completed(user).code, rating=3, text="O'rtacha")
    services.set_status(review, Review.Status.PUBLISHED)
    res = agency_api.post(
        f"/api/v1/cabinet/reviews/{review.id}/reply/", {"text": "Rahmat, tuzatamiz"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["agency_reply"] == "Rahmat, tuzatamiz"
    assert APIClient().get("/api/v1/reviews/").data["results"][0]["agency_reply"] == "Rahmat, tuzatamiz"


def test_other_agency_cannot_reply(user, completed, samarqand):
    from apps.agencies.models import Agency, AgencyMember

    review = services.create_review(user=user, booking_code=completed(user).code, rating=3)
    other = Agency.objects.create(name="B", slug="b")
    u = User.objects.create_user(email="b@example.com", password=PASSWORD)
    AgencyMember.objects.create(agency=other, user=u)
    client = APIClient()
    client.force_authenticate(u)
    assert (
        client.post(f"/api/v1/cabinet/reviews/{review.id}/reply/", {"text": "x"}, format="json").status_code
        == 404
    )
