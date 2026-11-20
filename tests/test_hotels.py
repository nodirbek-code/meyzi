from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.hotels import services
from apps.hotels.models import Hotel, HotelBooking, HotelMember, RoomType

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

IN = timezone.localdate() + timedelta(days=10)
OUT = IN + timedelta(days=2)


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="hotel@example.com", password=PASSWORD)


@pytest.fixture
def owner_api(owner):
    c = APIClient()
    c.force_authenticate(owner)
    return c


@pytest.fixture
def hotel(owner, samarqand):
    h = Hotel.objects.create(
        name="Registon Plaza",
        slug="registon-plaza",
        destination=samarqand,
        address="Samarqand",
        phone="+998662000000",
        stars=4,
        amenities=["wifi", "breakfast"],
        status=Hotel.Status.APPROVED,
    )
    HotelMember.objects.create(hotel=h, user=owner, role="owner")
    return h


@pytest.fixture
def room(hotel):
    return RoomType.objects.create(
        hotel=hotel, name="Standart", capacity=2, price_per_night_uzs=600_000, total_rooms=3
    )


def book(user, room, **kw):
    data = dict(
        user=user,
        room_type_id=room.pk,
        check_in=IN,
        check_out=OUT,
        rooms=1,
        guests=2,
        contact_name="Ali",
        contact_phone="+998900000000",
    )
    data.update(kw)
    return services.create_booking(**data)


def other_user(n=1):
    return User.objects.create_user(email=f"u{n}@example.com", password=PASSWORD)


# ---------- Ariza ----------


def test_register_hotel_flow(auth_api, user, samarqand):
    res = auth_api.post(
        "/api/v1/hotels/me/",
        {
            "name": "Bibi Guest House",
            "kind": "guesthouse",
            "destination": "samarqand",
            "address": "Samarqand, Registon ko'chasi",
            "phone": "+998901234567",
            "amenities": ["wifi", "wifi", "ac"],
            "status": "approved",
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    assert (res.data["status"], res.data["slug"], res.data["amenities"]) == (
        "pending",
        "bibi-guest-house",
        ["wifi", "ac"],
    )
    user.refresh_from_db()
    assert user.role == User.Role.BUSINESS
    assert APIClient().get("/api/v1/hotels/").data["count"] == 0  # tasdiqlanmagan
    assert auth_api.post("/api/v1/hotels/me/", {"name": "2"}, format="json").status_code == 400

    services.approve_hotel(Hotel.objects.get(slug="bibi-guest-house"))
    # xona turi yo'q bo'lsa ham ro'yxatda, narxi null
    assert APIClient().get("/api/v1/hotels/").data["results"][0]["min_price_uzs"] is None


# ---------- Qidiruv va bo'sh xonalar ----------


def test_search_filters(api, hotel, room):
    def slugs(q=""):
        return [h["slug"] for h in api.get(f"/api/v1/hotels/{q}").data["results"]]

    assert slugs() == ["registon-plaza"]
    assert api.get("/api/v1/hotels/").data["results"][0]["min_price_uzs"] == 600_000
    assert slugs("?destination=samarqand&stars=4&amenity=wifi") == ["registon-plaza"]
    assert slugs("?stars=5") == []
    assert slugs("?amenity=pool") == []
    assert slugs("?max_price=500000") == []


def test_availability_counts_overlapping_nights(user, room):
    book(user, room, rooms=2)  # IN..OUT
    book(
        other_user(1), room, check_in=OUT, check_out=OUT + timedelta(days=1), rooms=3
    )  # keyingi kecha — kesishmaydi
    free = services.availability([room], IN, OUT)[room.pk]
    assert free == 1
    assert services.availability([room], OUT - timedelta(days=1), OUT + timedelta(days=1))[room.pk] == 0


def test_search_by_dates(api, user, hotel, room):
    url = f"/api/v1/hotels/?check_in={IN}&check_out={OUT}&guests=2&rooms=1"
    assert api.get(url).data["count"] == 1
    book(user, room, rooms=3)
    assert api.get(url).data["count"] == 0  # hammasi band
    assert (
        api.get(f"/api/v1/hotels/?check_in={IN}&check_out={OUT}&guests=5&rooms=2").data["count"] == 0
    )  # sig'im


def test_rooms_endpoint_with_dates(api, user, hotel, room):
    book(user, room, rooms=1)
    offers = api.get(f"/api/v1/hotels/registon-plaza/rooms/?check_in={IN}&check_out={OUT}").data
    assert offers[0]["available_rooms"] == 2
    assert (offers[0]["nights"], offers[0]["stay_total_uzs"]) == (2, 1_200_000)
    plain = api.get("/api/v1/hotels/registon-plaza/rooms/").data
    assert plain[0]["available_rooms"] is None


def test_bad_dates(api, hotel):
    assert api.get(f"/api/v1/hotels/?check_in={OUT}&check_out={IN}").status_code == 400
    assert api.get(f"/api/v1/hotels/?check_in={IN}").status_code == 400


# ---------- Bron ----------


def test_create_booking_api(auth_api, hotel, room):
    res = auth_api.post(
        "/api/v1/hotel-bookings/",
        {
            "room_type": room.pk,
            "check_in": str(IN),
            "check_out": str(OUT),
            "rooms": 2,
            "guests": 3,
            "contact_name": "Ali",
            "contact_phone": "+998900000000",
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    assert res.data["code"].startswith("LH")
    assert (res.data["nights"], res.data["total_uzs"], res.data["status"]) == (
        2,
        2_400_000,
        "pending_payment",
    )
    b = HotelBooking.objects.get(code=res.data["code"])
    assert (b.commission_uzs, b.hotel_amount_uzs) == (360_000, 2_040_000)
    local = timezone.localtime(b.check_in_at)
    assert (local.date(), local.hour) == (IN, 14)


@pytest.mark.parametrize(
    ("kw", "field"),
    [
        ({"rooms": 4}, "rooms"),
        ({"guests": 3}, "guests"),
        ({"check_out": IN}, "check_out"),
        ({"check_in": timezone.localdate() - timedelta(days=1)}, "check_in"),
        ({"check_out": IN + timedelta(days=31)}, "check_out"),
    ],
)
def test_booking_validation(user, room, kw, field):
    with pytest.raises(ValidationError) as exc:
        book(user, room, **kw)
    assert field in exc.value.detail


def test_cannot_overbook(user, room):
    book(user, room, rooms=3)
    with pytest.raises(ValidationError):
        book(other_user(), room, rooms=1)


def test_expired_hold_frees_rooms(user, room):
    b = book(user, room, rooms=3)
    HotelBooking.objects.filter(pk=b.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert book(other_user(), room, rooms=3).status == "pending_payment"  # eskirgani ushlab turmaydi
    assert services.expire_due() == 1


def test_unapproved_hotel_not_bookable(user, hotel, room):
    hotel.status = Hotel.Status.SUSPENDED
    hotel.save()
    with pytest.raises(ValidationError):
        book(user, room)


def test_mark_paid_and_expired(user, room):
    b = services.mark_paid(book(user, room))
    assert (b.status, b.expires_at) == ("confirmed", None)
    b2 = book(other_user(), room)
    HotelBooking.objects.filter(pk=b2.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(ValidationError):
        services.mark_paid(b2)


# ---------- Bekor qilish ----------


@pytest.mark.parametrize(
    ("policy", "hours", "refund"), [("free", 30, 1_200_000), ("free", 10, 0), ("partial", 72, 600_000)]
)
def test_tourist_cancel(user, hotel, room, policy, hours, refund):
    hotel.cancellation_policy = policy
    hotel.save()
    b = services.mark_paid(book(user, room))
    HotelBooking.objects.filter(pk=b.pk).update(check_in_at=timezone.now() + timedelta(hours=hours))
    b.refresh_from_db()
    assert services.cancel(b, by="tourist").refund_uzs == refund
    assert services.availability([room], IN, OUT)[room.pk] == 3


def test_hotel_cancels_full_refund(owner_api, user, hotel, room):
    hotel.cancellation_policy = "non_refundable"
    hotel.save()
    b = services.mark_paid(book(user, room))
    res = owner_api.post(
        f"/api/v1/cabinet/hotel/bookings/{b.code}/cancel/", {"reason": "Ta'mir"}, format="json"
    )
    assert res.status_code == 200
    assert (res.data["refund_uzs"], res.data["cancelled_by"]) == (1_200_000, "hotel")


def test_cancel_preview_api(auth_api, user, room):
    b = services.mark_paid(book(user, room))
    res = auth_api.get(f"/api/v1/hotel-bookings/{b.code}/cancel-preview/")
    assert res.data == {"can_cancel": True, "refund_uzs": 1_200_000}


# ---------- Kabinet ----------


def test_cabinet_rooms_and_bookings(owner_api, auth_api, user, hotel, room):
    res = owner_api.post(
        "/api/v1/cabinet/hotel/rooms/",
        {
            "name": "Lyuks",
            "capacity": 3,
            "price_per_night_uzs": 1_200_000,
            "total_rooms": 1,
            "amenities": ["ac"],
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    assert len(owner_api.get("/api/v1/cabinet/hotel/rooms/").data) == 2

    b = book(user, room)
    rows = owner_api.get("/api/v1/cabinet/hotel/bookings/").data["results"]
    assert [r["code"] for r in rows] == [b.code]
    assert rows[0]["hotel_amount_uzs"] == 1_020_000
    assert owner_api.delete(f"/api/v1/cabinet/hotel/rooms/{room.pk}/").status_code == 400  # bronlari bor

    assert auth_api.get("/api/v1/cabinet/hotel/rooms/").status_code == 403


def test_other_hotel_isolated(owner_api, samarqand, user):
    other = Hotel.objects.create(
        name="Boshqa", slug="boshqa", destination=samarqand, address="x", phone="1", status="approved"
    )
    rt = RoomType.objects.create(hotel=other, name="X", capacity=2, price_per_night_uzs=1, total_rooms=1)
    b = book(user, rt)
    assert (
        owner_api.get(f"/api/v1/cabinet/hotel/bookings/{b.code}/").status_code == 403
    )  # o'z mehmonxonasi yo'q
    assert (
        owner_api.patch(f"/api/v1/cabinet/hotel/rooms/{rt.pk}/", {"name": "Y"}, format="json").status_code
        == 403
    )


def test_owner_cannot_touch_other_hotel_rooms(owner_api, hotel, samarqand):
    other = Hotel.objects.create(
        name="B", slug="b", destination=samarqand, address="x", phone="1", status="approved"
    )
    rt = RoomType.objects.create(hotel=other, name="X", capacity=2, price_per_night_uzs=1, total_rooms=1)
    assert (
        owner_api.patch(f"/api/v1/cabinet/hotel/rooms/{rt.pk}/", {"name": "Y"}, format="json").status_code
        == 404
    )


# ---------- Sharhlar ----------


def test_review_after_stay(auth_api, owner_api, user, hotel, room):
    b = services.mark_paid(book(user, room))
    url = f"/api/v1/hotel-bookings/{b.code}/review/"
    assert auth_api.post(url, {"rating": 5}, format="json").status_code == 400
    assert services.complete_finished(today=OUT) == 1
    assert auth_api.post(url, {"rating": 4, "text": "Toza"}, format="json").status_code == 201
    hotel.refresh_from_db()
    assert (hotel.rating, hotel.reviews_count) == (Decimal("4.00"), 1)

    review_id = owner_api.get("/api/v1/cabinet/hotel/reviews/").data["results"][0]["id"]
    owner_api.post(f"/api/v1/cabinet/hotel/reviews/{review_id}/reply/", {"text": "Rahmat!"}, format="json")
    assert (
        APIClient().get("/api/v1/hotels/registon-plaza/reviews/").data["results"][0]["hotel_reply"]
        == "Rahmat!"
    )
