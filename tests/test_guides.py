from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.guides import policies, services
from apps.guides.models import GuideBooking, GuideMeetingPoint, GuideProfile, GuideUnavailableDate

from .conftest import PASSWORD, phone_token
from .media_samples import JPEG, PDF

pytestmark = pytest.mark.django_db


@pytest.fixture
def guide_user(db):
    return User.objects.create_user(email="gid@example.com", password=PASSWORD, first_name="Aziz")


@pytest.fixture
def guide(guide_user, samarqand):
    g = GuideProfile.objects.create(
        user=guide_user,
        slug="aziz",
        display_name="Aziz",
        phone="+998901112233",
        languages=["uz", "en", "de"],
        specializations=["history"],
        price_half_day_uzs=300_000,
        price_full_day_uzs=500_000,
        price_per_day_uzs=450_000,
        status=GuideProfile.Status.APPROVED,
    )
    g.destinations.add(samarqand)
    GuideMeetingPoint.objects.create(
        guide=g,
        destination=samarqand,
        name="Registon",
        address="Registon maydoni, Samarqand",
        latitude="39.654167",
        longitude="66.959722",
    )
    return g


@pytest.fixture
def guide_api(guide_user):
    c = APIClient()
    c.force_authenticate(guide_user)
    return c


DAY = timezone.localdate() + timedelta(days=10)


def request(user, guide, samarqand, **kw):
    data = dict(
        user=user,
        guide=guide,
        destination=samarqand,
        duration="full_day",
        start_date=DAY,
        start_time=time(9, 0),
        days=1,
        group_size=2,
        language="en",
        meeting_point=guide.meeting_points.first(),
        contact_name="Ali",
        contact_phone="+998900000000",
    )
    data.update(kw)
    return services.request_booking(**data)


def confirmed(user, guide, samarqand, hours_before=None, **kw):
    b = request(user, guide, samarqand, **kw)
    services.accept(b)
    b = services.mark_paid(b)
    if hours_before is not None:
        GuideBooking.objects.filter(pk=b.pk).update(starts_at=timezone.now() + timedelta(hours=hours_before))
        b.refresh_from_db()
    return b


# ---------- Qoidalar (taqdimot) ----------


@pytest.mark.parametrize(
    ("hours", "ratio"), [(48, "1"), (47.9, "0.5"), (24, "0.5"), (23.9, "0.25"), (12, "0.25"), (11, "0")]
)
def test_tourist_refund_ratio(hours, ratio):
    assert policies.tourist_refund_ratio(timedelta(hours=hours)) == Decimal(ratio)


@pytest.mark.parametrize(
    ("hours", "penalty", "warnings"),
    [(72, 0, 0), (71, 5, 0), (48, 5, 0), (47, 10, 1), (24, 10, 1), (23, 20, 2)],
)
def test_guide_penalty(hours, penalty, warnings):
    assert policies.guide_cancel_penalty(timedelta(hours=hours)) == (Decimal(penalty), warnings)


# ---------- Narx ----------


def test_quote(api, guide):
    q = api.get("/api/v1/guides/aziz/quote/?duration=full_day&group_size=2").data
    assert (q["total_uzs"], q["surcharge_uzs"]) == (500_000, 0)
    q = api.get("/api/v1/guides/aziz/quote/?duration=full_day&group_size=5").data
    assert (q["base_uzs"], q["surcharge_uzs"], q["total_uzs"]) == (500_000, 100_000, 600_000)  # +20%
    q = api.get("/api/v1/guides/aziz/quote/?duration=multi_day&days=3&group_size=1").data
    assert q["total_uzs"] == 1_350_000
    q = api.get("/api/v1/guides/aziz/quote/?duration=half_day&days=5").data
    assert (q["days"], q["total_uzs"]) == (1, 300_000)


# ---------- Profil va ariza ----------


def test_become_guide_flow(auth_api, user, admin_api, samarqand):
    payload = {
        "display_name": "Ali Gid",
        "phone": "+998901234567",
        "phone_token": phone_token("+998901234567"),
        "languages": ["uz", "ru", "uz"],
        "destinations": ["samarqand"],
        "price_half_day_uzs": 200000,
        "price_full_day_uzs": 350000,
        "price_per_day_uzs": 300000,
    }
    res = auth_api.post("/api/v1/guides/me/", payload, format="multipart")
    assert res.status_code == 400 and {"photo", "certificate_file"} <= set(res.data)  # rasm, sertifikat shart
    payload |= {
        "photo": SimpleUploadedFile("men.jpg", JPEG, content_type="image/jpeg"),
        "certificate_file": SimpleUploadedFile("sertifikat.pdf", PDF, content_type="application/pdf"),
    }
    res = auth_api.post("/api/v1/guides/me/", payload, format="multipart")
    assert res.status_code == 201, res.data
    assert res.data["status"] == "pending"
    assert res.data["languages"] == ["uz", "ru"]
    user.refresh_from_db()
    assert user.role == User.Role.GUIDE
    payload["photo"].seek(0)
    payload["certificate_file"].seek(0)
    assert auth_api.post("/api/v1/guides/me/", payload, format="multipart").status_code == 400

    # tekshiruvda — katalogda yo'q, status o'zgartirib bo'lmaydi
    assert APIClient().get("/api/v1/guides/").data["count"] == 0
    auth_api.patch("/api/v1/guides/me/", {"status": "approved", "commission_percent": "1"}, format="json")
    profile = GuideProfile.objects.get(user=user)
    assert (profile.status, profile.commission_percent) == ("pending", Decimal("15"))

    services.approve_profile(profile)
    assert APIClient().get("/api/v1/guides/").data["count"] == 1


def test_profile_validation(auth_api, samarqand):
    res = auth_api.post(
        "/api/v1/guides/me/",
        {"display_name": "X", "phone": "1", "languages": ["xx"], "destinations": [], "price_half_day_uzs": 0},
        format="json",
    )
    assert res.status_code == 400
    assert {"languages", "destinations", "price_full_day_uzs"} <= set(res.data)


# ---------- Ommaviy katalog ----------


def test_guide_list_filters(api, guide, samarqand, user):
    def slugs(q=""):
        return [g["slug"] for g in api.get(f"/api/v1/guides/{q}").data["results"]]

    assert slugs() == ["aziz"]
    assert slugs("?destination=samarqand") == ["aziz"]
    assert slugs("?destination=buxoro") == []
    assert slugs("?language=de") == ["aziz"]
    assert slugs("?language=zh") == []
    assert slugs("?specialization=history") == ["aziz"]
    assert slugs("?max_price=400000") == []
    assert slugs(f"?date={DAY}") == ["aziz"]

    request(user, guide, samarqand)
    assert slugs(f"?date={DAY}") == []  # shu kuni band
    assert str(DAY) in api.get("/api/v1/guides/aziz/busy-dates/").data["busy_dates"]


def test_multi_day_blocks_all_days(api, guide, samarqand, user):
    request(user, guide, samarqand, duration="multi_day", days=3)
    busy = api.get("/api/v1/guides/aziz/busy-dates/").data["busy_dates"]
    assert [str(DAY + timedelta(days=i)) for i in range(3)] == busy
    assert [
        g["slug"] for g in api.get(f"/api/v1/guides/?date={DAY + timedelta(days=2)}").data["results"]
    ] == []


# ---------- Bron so'rovi ----------


def test_request_booking_api(auth_api, guide, samarqand):
    res = auth_api.post(
        "/api/v1/guide-bookings/",
        {
            "guide": "aziz",
            "destination": "samarqand",
            "duration": "full_day",
            "start_date": str(DAY),
            "start_time": "09:00",
            "group_size": 6,
            "language": "en",
            "meeting_point": guide.meeting_points.get().pk,
            "contact_name": "Ali",
            "contact_phone": "+998900000000",
            "phone_token": phone_token("+998900000000"),
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    assert res.data["code"].startswith("LG")
    assert res.data["status"] == "requested"
    assert res.data["total_uzs"] == 600_000  # 6 kishi — +20%
    assert res.data["guide"]["phone"] is None  # to'lovdan oldin kontakt berilmaydi
    b = GuideBooking.objects.get(code=res.data["code"])
    assert (b.commission_uzs, b.guide_amount_uzs) == (90_000, 510_000)  # 15% / 85%


@pytest.mark.parametrize(
    ("kw", "field"),
    [
        ({"language": "zh"}, "language"),
        ({"group_size": 11}, "group_size"),
        ({"duration": "multi_day", "days": 1}, "days"),
        ({"start_date": timezone.localdate()}, "start_date"),
    ],
)
def test_request_validation(user, guide, samarqand, kw, field):
    with pytest.raises(ValidationError) as exc:
        request(user, guide, samarqand, **kw)
    assert field in exc.value.detail


def test_cannot_book_busy_or_unapproved(user, guide, samarqand):
    from apps.catalog.models import Destination

    GuideUnavailableDate.objects.create(guide=guide, date=DAY)
    with pytest.raises(ValidationError):
        request(user, guide, samarqand)
    with pytest.raises(ValidationError):
        request(
            user,
            guide,
            Destination.objects.create(name="Buxoro", slug="buxoro"),
            start_date=DAY + timedelta(1),
        )
    guide.status = GuideProfile.Status.SUSPENDED
    guide.save()
    with pytest.raises(ValidationError):
        request(user, guide, samarqand, start_date=DAY + timedelta(days=1))


def test_guide_cannot_book_self(guide_user, guide, samarqand):
    with pytest.raises(ValidationError):
        request(guide_user, guide, samarqand)


# ---------- Gid javobi ----------


def test_guide_accepts_then_admin_marks_paid(guide_api, auth_api, user, guide, samarqand):
    b = request(user, guide, samarqand)
    res = guide_api.get("/api/v1/cabinet/guide/bookings/")
    assert [x["code"] for x in res.data["results"]] == [b.code]
    assert res.data["results"][0]["contact_phone"] is None

    assert guide_api.post(f"/api/v1/cabinet/guide/bookings/{b.code}/accept/").data["status"] == "accepted"
    services.mark_paid(b)
    detail = auth_api.get(f"/api/v1/guide-bookings/{b.code}/").data
    assert detail["status"] == "confirmed"
    assert detail["guide"]["phone"] == "+998901112233"  # endi kontakt ochiq


def test_guide_declines(guide_api, user, guide, samarqand):
    b = request(user, guide, samarqand)
    res = guide_api.post(
        f"/api/v1/cabinet/guide/bookings/{b.code}/decline/", {"reason": "Band"}, format="json"
    )
    assert res.data["status"] == "declined"
    assert services.busy_dates(guide, start=DAY, end=DAY) == set()


def test_request_expires_if_no_answer(user, guide, samarqand):
    b = request(user, guide, samarqand)
    assert services.expire_requests(now=timezone.now() + timedelta(hours=25)) == 1
    b.refresh_from_db()
    assert b.status == "expired"
    with pytest.raises(ValidationError):
        services.accept(b)


def test_other_user_cannot_access(guide, samarqand, user):
    b = request(user, guide, samarqand)
    stranger = APIClient()
    stranger.force_authenticate(User.objects.create_user(email="s@example.com", password=PASSWORD))
    assert stranger.get(f"/api/v1/guide-bookings/{b.code}/").status_code == 404
    assert stranger.post(f"/api/v1/cabinet/guide/bookings/{b.code}/accept/").status_code == 403


# ---------- Bekor qilish ----------


@pytest.mark.parametrize(("hours", "refund"), [(50, 500_000), (30, 250_000), (15, 125_000), (5, 0)])
def test_tourist_cancel_refund(user, guide, samarqand, hours, refund):
    b = confirmed(user, guide, samarqand, hours_before=hours)
    b = services.cancel(b, by=GuideBooking.CancelledBy.TOURIST)
    assert (b.status, b.refund_uzs) == ("cancelled", refund)


def test_tourist_cancel_unpaid_refunds_nothing(user, guide, samarqand):
    b = services.cancel(request(user, guide, samarqand), by=GuideBooking.CancelledBy.TOURIST)
    assert b.refund_uzs == 0


def test_guide_cancel_penalty_and_full_refund(guide_api, user, guide, samarqand):
    b = confirmed(user, guide, samarqand, hours_before=30)
    res = guide_api.post(
        f"/api/v1/cabinet/guide/bookings/{b.code}/cancel/", {"reason": "Kasal"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["refund_uzs"] == 500_000
    assert (Decimal(res.data["guide_penalty_usd"]), res.data["guide_warnings"]) == (Decimal("10"), 1)
    guide.refresh_from_db()
    assert guide.warnings_count == 1


def test_guide_must_decline_not_cancel_request(guide_api, user, guide, samarqand):
    b = request(user, guide, samarqand)
    assert guide_api.post(f"/api/v1/cabinet/guide/bookings/{b.code}/cancel/").status_code == 400


# ---------- Kelmay qolish ----------


def test_tourist_no_show(guide_api, user, guide, samarqand):
    b = confirmed(user, guide, samarqand, hours_before=-0.5)
    url = f"/api/v1/cabinet/guide/bookings/{b.code}/tourist-no-show/"
    assert guide_api.post(url).status_code == 400  # 1 soat kutish kerak
    GuideBooking.objects.filter(pk=b.pk).update(starts_at=timezone.now() - timedelta(hours=1, minutes=1))
    res = guide_api.post(url)
    assert res.data["status"] == "completed"
    assert res.data["no_show"] == "tourist"
    assert (res.data["refund_uzs"], res.data["guide_amount_uzs"]) == (0, 150_000)  # 30%


def test_three_guide_no_shows_suspend(user, guide, samarqand):
    for i in range(3):
        b = confirmed(user, guide, samarqand, start_date=DAY + timedelta(days=i))
        b = services.report_guide_no_show(b)
        assert (b.refund_uzs, b.guide_penalty_usd) == (500_000, Decimal("25"))
    guide.refresh_from_db()
    assert (guide.no_show_count, guide.status) == (3, "suspended")


# ---------- Sharhlar ----------


def test_review_after_completion(auth_api, user, guide, samarqand):
    b = confirmed(user, guide, samarqand)
    url = f"/api/v1/guide-bookings/{b.code}/review/"
    assert auth_api.post(url, {"rating": 5}, format="json").status_code == 400  # hali yakunlanmagan

    services.complete_finished(now=b.starts_at + timedelta(days=1, minutes=1))
    res = auth_api.post(url, {"rating": 5, "text": "Ajoyib gid"}, format="json")
    assert res.status_code == 201, res.data
    assert auth_api.post(url, {"rating": 4}, format="json").status_code == 400
    guide.refresh_from_db()
    assert (guide.rating, guide.reviews_count) == (Decimal("5.00"), 1)
    assert APIClient().get("/api/v1/guides/aziz/reviews/").data["results"][0]["text"] == "Ajoyib gid"


def test_low_rating_suspends_after_min_reviews(guide, samarqand):
    for i in range(policies.LOW_RATING_MIN_REVIEWS):
        u = User.objects.create_user(email=f"r{i}@example.com", password=PASSWORD)
        b = confirmed(u, guide, samarqand, start_date=DAY + timedelta(days=i))
        GuideBooking.objects.filter(pk=b.pk).update(status="completed")
        b.refresh_from_db()
        services.create_review(user=u, booking=b, rating=3)
    guide.refresh_from_db()
    assert guide.rating == Decimal("3.00")
    assert guide.status == "suspended"


# ---------- Band kunlar ----------


def test_unavailable_dates(guide_api, user, guide, samarqand):
    url = "/api/v1/cabinet/guide/unavailable-dates/"
    assert guide_api.post(url, {"date": str(DAY + timedelta(days=5))}, format="json").status_code == 201
    assert guide_api.post(url, {"date": str(DAY + timedelta(days=5))}, format="json").status_code == 400
    request(user, guide, samarqand)
    assert guide_api.post(url, {"date": str(DAY)}, format="json").status_code == 400  # bron bor
    assert len(guide_api.get(url).data) == 1


def test_starts_at_is_local(user, guide, samarqand):
    b = request(user, guide, samarqand, start_time=time(6, 30))
    local = timezone.localtime(b.starts_at)
    assert (local.date(), local.time()) == (DAY, time(6, 30))
    assert isinstance(b.starts_at, datetime)
