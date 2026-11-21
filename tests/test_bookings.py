from datetime import time, timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.bookings import services
from apps.bookings.models import Booking
from apps.tours.models import Departure, Tour

from .conftest import PASSWORD, phone_token

pytestmark = pytest.mark.django_db

CONTACT = {"contact_name": "Ali Valiyev", "contact_phone": "+998901234567"}
# API orqali: telefon Telegram kodi bilan tasdiqlangan bo'lishi shart
API_CONTACT = {**CONTACT, "phone_token": phone_token("+998901234567")}


@pytest.fixture
def book(user, departure):
    """Bron yaratuvchi yordamchi (service orqali)."""

    def _book(seats=2, who=None, dep=None, **extra):
        return services.create_booking(
            user=who or user, departure_id=(dep or departure).pk, seats=seats, **{**CONTACT, **extra}
        )

    return _book


def seats_booked(departure):
    departure.refresh_from_db()
    return departure.seats_booked


# ---------- Yaratish ----------


def test_create_booking_api(auth_api, departure, tour):
    res = auth_api.post(
        "/api/v1/bookings/",
        {
            "departure": departure.id,
            "seats": 2,
            **API_CONTACT,
            "travelers": [{"full_name": "A"}, {"full_name": "B"}],
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    assert res.data["code"].startswith("LZ")
    assert res.data["status"] == "pending_payment"
    assert res.data["total_uzs"] == 2 * 890_000
    assert res.data["installment"]["monthly_uzs"] == 213_600
    assert len(res.data["travelers"]) == 2
    expires = timezone.datetime.fromisoformat(res.data["expires_at"])
    assert timedelta(minutes=29) < expires - timezone.now() <= timedelta(minutes=30)
    assert seats_booked(departure) == 2


def test_booking_requires_login(api, departure):
    res = api.post("/api/v1/bookings/", {"departure": departure.id, "seats": 1, **API_CONTACT}, format="json")
    assert res.status_code == 401


def test_price_and_commission_frozen(book, departure, agency):
    departure.price_uzs = 700_000
    departure.save()
    booking = book(seats=3)
    assert booking.unit_price_uzs == 700_000
    assert booking.total_uzs == 2_100_000
    assert booking.commission_percent == 15
    assert booking.commission_uzs == 315_000
    assert booking.agency_amount_uzs == 1_785_000

    # keyin narx yoki komissiya o'zgarsa — bron o'zgarmaydi
    agency.commission_percent = 20
    agency.save()
    booking.refresh_from_db()
    assert booking.commission_uzs == 315_000


def test_departure_at_uses_tour_time(book, tour, departure):
    tour.departure_time = time(6, 30)
    tour.save()
    booking = book()
    local = timezone.localtime(booking.departure_at)
    assert (local.date(), local.time()) == (departure.date, time(6, 30))


def test_cannot_overbook(book, departure):
    book(seats=18)
    with pytest.raises(ValidationError) as exc:
        book(seats=3, who=User.objects.create_user(email="b@example.com", password=PASSWORD))
    assert "2 ta bo'sh joy" in str(exc.value.detail)
    assert seats_booked(departure) == 18


def test_travelers_count_must_match(book):
    with pytest.raises(ValidationError):
        book(seats=2, travelers=[{"full_name": "Faqat bitta"}])


@pytest.mark.parametrize(
    "breaker",
    [
        lambda t, d: setattr(d, "status", Departure.Status.CLOSED),
        lambda t, d: setattr(d, "date", timezone.localdate() - timedelta(days=1)),
        lambda t, d: Tour.objects.filter(pk=t.pk).update(status=Tour.Status.ARCHIVED),
    ],
)
def test_not_bookable(book, tour, departure, breaker):
    breaker(tour, departure)
    departure.save()
    with pytest.raises(ValidationError):
        book()


def test_pending_limit(book, settings, departure, tour):
    settings.LAZURI_MAX_PENDING_BOOKINGS = 2
    book(seats=1)
    book(seats=1)
    with pytest.raises(ValidationError):
        book(seats=1)


# ---------- 30 daqiqalik band qilish ----------


def test_hold_expires_and_releases_seats(book, departure):
    booking = book(seats=5)
    assert seats_booked(departure) == 5

    assert services.expire_due_bookings(now=timezone.now() + timedelta(minutes=29)) == 0
    assert services.expire_due_bookings(now=timezone.now() + timedelta(minutes=31)) == 1
    booking.refresh_from_db()
    assert booking.status == Booking.Status.EXPIRED
    assert seats_booked(departure) == 0


def test_expired_seats_reused_on_new_booking(book, departure):
    old = book(seats=20)
    Booking.objects.filter(pk=old.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    other = User.objects.create_user(email="c@example.com", password=PASSWORD)
    new = book(seats=20, who=other)  # eskisining joyi avtomatik bo'shaydi
    assert new.status == Booking.Status.PENDING_PAYMENT
    old.refresh_from_db()
    assert old.status == Booking.Status.EXPIRED
    assert seats_booked(departure) == 20


def test_detail_shows_expired(auth_api, book):
    booking = book()
    Booking.objects.filter(pk=booking.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    res = auth_api.get(f"/api/v1/bookings/{booking.code}/")
    assert res.data["status"] == "expired"


def test_confirm_booking(book):
    booking = services.confirm_booking(book())
    assert booking.status == Booking.Status.CONFIRMED
    assert booking.expires_at is None
    assert services.confirm_booking(booking).status == Booking.Status.CONFIRMED  # idempotent


def test_cannot_confirm_expired(book):
    booking = book()
    Booking.objects.filter(pk=booking.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(ValidationError):
        services.confirm_booking(booking)


# ---------- Bekor qilish ----------


def _confirmed(book, hours_before, policy="free", tour=None):
    booking = services.confirm_booking(book(seats=2))
    if tour:
        Tour.objects.filter(pk=tour.pk).update(cancellation_policy=policy)
    Booking.objects.filter(pk=booking.pk).update(
        cancellation_policy=policy, departure_at=timezone.now() + timedelta(hours=hours_before)
    )
    booking.refresh_from_db()
    return booking


@pytest.mark.parametrize(
    ("policy", "hours", "refund"),
    [
        ("free", 25, 1_780_000),
        ("free", 23, 0),
        ("partial", 49, 890_000),
        ("partial", 47, 0),
        ("non_refundable", 100, 0),
    ],
)
def test_tourist_cancel_refund(book, departure, policy, hours, refund):
    booking = _confirmed(book, hours, policy)
    booking = services.cancel_booking(booking, by=Booking.CancelledBy.TOURIST)
    assert booking.status == Booking.Status.CANCELLED
    assert booking.refund_uzs == refund
    assert seats_booked(departure) == 0


def test_cancel_pending_refunds_nothing(book, departure):
    booking = services.cancel_booking(book(), by=Booking.CancelledBy.TOURIST)
    assert booking.refund_uzs == 0
    assert seats_booked(departure) == 0


def test_agency_cancel_full_refund(book):
    booking = _confirmed(book, 2, "non_refundable")
    booking = services.cancel_booking(booking, by=Booking.CancelledBy.AGENCY)
    assert booking.refund_uzs == booking.total_uzs


def test_tourist_cannot_cancel_after_departure(book):
    booking = _confirmed(book, -1)
    with pytest.raises(ValidationError):
        services.cancel_booking(booking, by=Booking.CancelledBy.TOURIST)


def test_cancel_twice(book):
    booking = services.cancel_booking(book(), by=Booking.CancelledBy.TOURIST)
    with pytest.raises(ValidationError):
        services.cancel_booking(booking, by=Booking.CancelledBy.TOURIST)


def test_cancel_preview_and_cancel_api(auth_api, book):
    booking = _confirmed(book, 72, "partial")
    preview = auth_api.get(f"/api/v1/bookings/{booking.code}/cancel-preview/").data
    assert preview == {
        "can_cancel": True,
        "refund_uzs": 890_000,
        "cancellation_policy": "partial",
        "policy_text": preview["policy_text"],
    }
    res = auth_api.post(
        f"/api/v1/bookings/{booking.code}/cancel/", {"reason": "Rejam o'zgardi"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["status"] == "cancelled"
    assert res.data["refund_uzs"] == 890_000
    assert res.data["cancelled_by"] == "tourist"


def test_user_sees_only_own_bookings(auth_api, book):
    other = User.objects.create_user(email="d@example.com", password=PASSWORD)
    mine = book()
    theirs = book(who=other)
    codes = [b["code"] for b in auth_api.get("/api/v1/bookings/").data["results"]]
    assert codes == [mine.code]
    assert auth_api.get(f"/api/v1/bookings/{theirs.code}/").status_code == 404


# ---------- Agentlik kabineti ----------


def test_cabinet_sees_agency_bookings(agency_api, book, samarqand, category):
    from apps.agencies.models import Agency

    booking = book()
    other_agency = Agency.objects.create(name="Boshqa", slug="boshqa")
    other_tour = Tour.objects.create(
        agency=other_agency,
        destination=samarqand,
        title="X",
        slug="x",
        price_uzs=100,
        status=Tour.Status.PUBLISHED,
    )
    other_dep = Departure.objects.create(
        tour=other_tour, date=timezone.localdate() + timedelta(days=3), seats_total=5
    )
    book(dep=other_dep)

    res = agency_api.get("/api/v1/cabinet/bookings/")
    assert [b["code"] for b in res.data["results"]] == [booking.code]
    assert res.data["results"][0]["agency_amount_uzs"] == booking.agency_amount_uzs
    assert res.data["results"][0]["user_email"] == "turist@example.com"


def test_cabinet_cancel_booking(agency_api, book):
    booking = _confirmed(book, 5, "non_refundable")
    res = agency_api.post(
        f"/api/v1/cabinet/bookings/{booking.code}/cancel/", {"reason": "Ob-havo"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["refund_uzs"] == booking.total_uzs
    assert res.data["cancelled_by"] == "agency"


def test_cancelling_departure_cancels_bookings(agency_api, book, tour, departure):
    paid = services.confirm_booking(book(seats=2))
    pending = book(seats=1)
    url = f"/api/v1/cabinet/tours/{tour.slug}/departures/{departure.id}/"
    assert agency_api.delete(url).status_code == 400  # bronli sana o'chirilmaydi

    res = agency_api.patch(url, {"status": "cancelled"}, format="json")
    assert res.status_code == 200
    paid.refresh_from_db()
    pending.refresh_from_db()
    assert (paid.status, paid.refund_uzs) == ("cancelled", paid.total_uzs)
    assert (pending.status, pending.refund_uzs) == ("cancelled", 0)
    assert seats_booked(departure) == 0


# ---------- Fon vazifasi ----------


def test_process_bookings_command(book, capsys):
    pending = book(seats=1)
    done = services.confirm_booking(book(seats=1))
    Booking.objects.filter(pk=pending.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
    Booking.objects.filter(pk=done.pk).update(departure_at=timezone.now() - timedelta(days=2))

    call_command("process_bookings")
    assert "expired: 1, completed: 1" in capsys.readouterr().out
    pending.refresh_from_db()
    done.refresh_from_db()
    assert pending.status == Booking.Status.EXPIRED
    assert done.status == Booking.Status.COMPLETED


def test_today_departure_not_bookable_after_start_time(tour, departure):
    from datetime import time as dtime

    from django.utils import timezone as tz

    departure.date = tz.localdate()
    departure.save()
    tour.departure_time = dtime(0, 0)
    tour.save()
    departure.refresh_from_db()
    assert departure.is_bookable is False  # 00:00 allaqachon o'tgan
    tour.departure_time = dtime(23, 59, 59)
    tour.save()
    departure.refresh_from_db()
    assert departure.is_bookable is (tz.localtime().time() < dtime(23, 59, 59))
