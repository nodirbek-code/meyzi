"""XATOLAR.md 1–5: telefon tasdiqlash (Telegram), uchrashuv joyi, bron kodi, Google orqali kirish."""

import json
from datetime import time, timedelta
from unittest import mock

import pytest
from django.core import mail, signing
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts import google
from apps.accounts.models import User
from apps.accounts.phones import TOKEN_SALT
from apps.guides import services as guide_services
from apps.guides.models import GuideBooking, GuideMeetingPoint, GuideProfile
from apps.notifications import sms, telegram_codes
from apps.notifications.models import UserMessage

from .conftest import PASSWORD, phone_token

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_outboxes():
    telegram_codes.outbox.clear()
    sms.outbox.clear()
    yield
    telegram_codes.outbox.clear()
    sms.outbox.clear()


# ---------- 1, 4. Telefon: +998 format, Telegram kod, tasdiqlangandan keyingina qabul ----------


def _check_phone(client, phone):
    res = client.post("/api/v1/auth/phone-check/send-code/", {"phone": phone}, format="json")
    assert res.status_code == 200, res.data
    assert res.data["channel"] == "telegram"
    code = telegram_codes.outbox[-1][1]
    res = client.post(
        "/api/v1/auth/phone-check/verify/", {"phone": res.data["phone"], "code": code}, format="json"
    )
    assert res.status_code == 200, res.data
    return res.data


def test_phone_check_flow_gives_token(api):
    data = _check_phone(api, "90 123 45 67")
    assert data["phone"] == "+998901234567"
    assert telegram_codes.outbox == [("+998901234567", telegram_codes.outbox[0][1])]
    assert not sms.outbox  # SMS emas — Telegram


def test_phone_check_wrong_code(api):
    api.post("/api/v1/auth/phone-check/send-code/", {"phone": "+998901234567"}, format="json")
    res = api.post(
        "/api/v1/auth/phone-check/verify/", {"phone": "+998901234567", "code": "000000"}, format="json"
    )
    assert res.status_code == 400


@pytest.mark.parametrize(
    "bad", ["abc", "+7 999 123 45 67", "90 123 45", "90 123 45 678", "+998 90 123 45 6a", "+998901234567;"]
)
def test_phone_format_rejected(api, bad):
    res = api.post("/api/v1/auth/phone-check/send-code/", {"phone": bad}, format="json")
    assert res.status_code == 400
    assert "phone" in res.data
    assert not telegram_codes.outbox


def test_booking_requires_verified_phone(auth_api, departure):
    base = {"departure": departure.id, "seats": 1, "contact_name": "Ali", "contact_phone": "+998901234567"}
    res = auth_api.post("/api/v1/bookings/", base, format="json")
    assert res.status_code == 400
    assert "contact_phone" in res.data

    # boshqa raqam uchun token yaramaydi
    res = auth_api.post(
        "/api/v1/bookings/", {**base, "phone_token": phone_token("+998909999999")}, format="json"
    )
    assert res.status_code == 400

    # soxta token
    res = auth_api.post("/api/v1/bookings/", {**base, "phone_token": "xyz"}, format="json")
    assert res.status_code == 400

    token = _check_phone(auth_api, "+998901234567")["phone_token"]
    res = auth_api.post("/api/v1/bookings/", {**base, "phone_token": token}, format="json")
    assert res.status_code == 201, res.data
    assert res.data["contact_phone"] == "+998901234567"


def test_booking_with_verified_account_phone_needs_no_token(auth_api, user, departure):
    user.phone, user.phone_verified = "+998901234567", True
    user.save()
    res = auth_api.post(
        "/api/v1/bookings/",
        {"departure": departure.id, "seats": 1, "contact_name": "Ali", "contact_phone": "90 123 45 67"},
        format="json",
    )
    assert res.status_code == 201, res.data
    assert res.data["contact_phone"] == "+998901234567"


def test_unverified_account_phone_still_needs_token(auth_api, user, departure):
    user.phone, user.phone_verified = "+998901234567", False
    user.save()
    res = auth_api.post(
        "/api/v1/bookings/",
        {"departure": departure.id, "seats": 1, "contact_name": "Ali", "contact_phone": "+998901234567"},
        format="json",
    )
    assert res.status_code == 400


def test_expired_phone_token(auth_api, departure, settings):
    token = phone_token("+998901234567")
    settings.LAZURI_PHONE_TOKEN_MAX_AGE = -1
    res = auth_api.post(
        "/api/v1/bookings/",
        {
            "departure": departure.id,
            "seats": 1,
            "contact_name": "Ali",
            "contact_phone": "+998901234567",
            "phone_token": token,
        },
        format="json",
    )
    assert res.status_code == 400


def test_phone_check_attaches_phone_to_account_without_phone(auth_api, user):
    _check_phone(auth_api, "+998901234567")
    user.refresh_from_db()
    assert (user.phone, user.phone_verified) == ("+998901234567", True)


def test_traveler_phone_format_checked(auth_api, departure):
    res = auth_api.post(
        "/api/v1/bookings/",
        {
            "departure": departure.id,
            "seats": 1,
            "contact_name": "Ali",
            "contact_phone": "+998901234567",
            "phone_token": phone_token("+998901234567"),
            "travelers": [{"full_name": "Vali", "phone": "salom"}],
        },
        format="json",
    )
    assert res.status_code == 400
    assert "travelers" in res.data


def test_agency_application_requires_verified_phone(api):
    data = {"agency_name": "Yangi", "contact_person": "Aziz", "phone": "+998901234567"}
    assert api.post("/api/v1/agencies/applications/", data, format="json").status_code == 400
    data["phone_token"] = phone_token("+998901234567")
    res = api.post("/api/v1/agencies/applications/", data, format="json")
    assert res.status_code == 201, res.data
    assert "phone_token" not in res.data


def test_cabinet_agency_phone_change_needs_code(agency_api, agency):
    agency.phone = "+998711234567"
    agency.save()
    # o'zgarmagan raqam — kod shart emas
    res = agency_api.patch("/api/v1/cabinet/agency/", {"phone": "+998 71 123 45 67"}, format="json")
    assert res.status_code == 200, res.data
    res = agency_api.patch("/api/v1/cabinet/agency/", {"phone": "+998712222222"}, format="json")
    assert res.status_code == 400
    res = agency_api.patch(
        "/api/v1/cabinet/agency/",
        {"phone": "+998712222222", "phone_token": phone_token("+998712222222")},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["phone"] == "+998712222222"


def test_telegram_delivery_failure_returns_503_and_allows_retry(api, settings):
    settings.TELEGRAM_CODE_BACKEND = "gateway"
    settings.TELEGRAM_GATEWAY_TOKEN = ""  # sozlanmagan → yuborib bo'lmaydi
    res = api.post("/api/v1/auth/phone/request-code/", {"phone": "+998901234567"}, format="json")
    assert res.status_code == 503
    settings.TELEGRAM_CODE_BACKEND = "locmem"
    res = api.post("/api/v1/auth/phone/request-code/", {"phone": "+998901234567"}, format="json")
    assert res.status_code == 200  # "60 soniya kuting" cheklovi yoqilmagan


def test_telegram_gateway_request(settings):
    settings.TELEGRAM_CODE_BACKEND = "gateway"
    settings.TELEGRAM_GATEWAY_TOKEN = "tg-token"
    captured = {}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"ok": True, "result": {"request_id": "r1"}}).encode()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["auth"] = req.get_header("Authorization")
        captured["body"] = json.loads(req.data)
        return Resp()

    with mock.patch("urllib.request.urlopen", fake_urlopen):
        telegram_codes.send_code("+998901234567", "123456", ttl_seconds=600)
    assert captured == {
        "url": "https://gatewayapi.telegram.org/sendVerificationMessage",
        "auth": "Bearer tg-token",
        "body": {"phone_number": "+998901234567", "code": "123456", "ttl": 600},
    }


def test_telegram_gateway_error(settings):
    settings.TELEGRAM_CODE_BACKEND = "gateway"
    settings.TELEGRAM_GATEWAY_TOKEN = "tg-token"

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": false, "error": "PHONE_NUMBER_INVALID"}'

    with mock.patch("urllib.request.urlopen", lambda req, timeout: Resp()):
        with pytest.raises(telegram_codes.CodeDeliveryError, match="PHONE_NUMBER_INVALID"):
            telegram_codes.send_code("+998901234567", "123456", ttl_seconds=600)


def test_features_say_telegram(api):
    res = api.get("/api/v1/features/")
    assert res.data["phone_verification"] == {"channel": "telegram", "country_code": "+998", "digits": 9}
    assert res.data["google_login"] == {"enabled": False, "client_id": None}


# ---------- 2. Uchrashuv joyi ----------


@pytest.fixture
def guide(samarqand):
    gu = User.objects.create_user(email="gid@example.com", password=PASSWORD)
    g = GuideProfile.objects.create(
        user=gu,
        slug="aziz",
        display_name="Aziz",
        phone="+998901112233",
        languages=["en"],
        price_half_day_uzs=300_000,
        price_full_day_uzs=500_000,
        price_per_day_uzs=450_000,
        status=GuideProfile.Status.APPROVED,
    )
    g.destinations.add(samarqand)
    return g


@pytest.fixture
def guide_api(guide):
    c = APIClient()
    c.force_authenticate(guide.user)
    return c


POINT = {
    "destination": "samarqand",
    "name": "Registon",
    "address": "Registon maydoni",
    "latitude": "39.654167",
    "longitude": "66.959722",
}


def test_guide_manages_meeting_points(guide_api, guide, api):
    res = guide_api.post("/api/v1/cabinet/guide/meeting-points/", POINT, format="json")
    assert res.status_code == 201, res.data
    assert guide_api.post("/api/v1/cabinet/guide/meeting-points/", POINT, format="json").status_code == 400
    res2 = guide_api.post(
        "/api/v1/cabinet/guide/meeting-points/", {**POINT, "destination": "yoq-shahar"}, format="json"
    )
    assert res2.status_code == 400
    res3 = guide_api.post(
        "/api/v1/cabinet/guide/meeting-points/",
        {k: v for k, v in POINT.items() if k != "latitude"},
        format="json",
    )
    assert res3.status_code == 400  # koordinata majburiy
    detail = api.get("/api/v1/guides/aziz/").data
    assert [p["name"] for p in detail["meeting_points"]] == ["Registon"]


def test_meeting_point_destination_must_be_guides_city(guide_api, guide, db):
    from apps.catalog.models import Destination

    Destination.objects.create(name="Buxoro", slug="buxoro", is_published=True)
    res = guide_api.post(
        "/api/v1/cabinet/guide/meeting-points/", {**POINT, "destination": "buxoro"}, format="json"
    )
    assert res.status_code == 400


def _guide_booking_payload(guide, point):
    return {
        "guide": guide.slug,
        "destination": "samarqand",
        "duration": "full_day",
        "start_date": str(timezone.localdate() + timedelta(days=10)),
        "start_time": "09:00",
        "group_size": 2,
        "language": "en",
        "meeting_point": point,
        "contact_name": "Ali",
        "contact_phone": "+998900000000",
        "phone_token": phone_token("+998900000000"),
    }


def test_tourist_cannot_type_own_meeting_point(auth_api, guide):
    res = auth_api.post(
        "/api/v1/guide-bookings/", _guide_booking_payload(guide, "Mening uyim"), format="json"
    )
    assert res.status_code == 400
    assert "meeting_point" in res.data


def test_tourist_picks_guides_meeting_point(auth_api, guide, samarqand):
    point = GuideMeetingPoint.objects.create(
        guide=guide, destination=samarqand, **{k: v for k, v in POINT.items() if k != "destination"}
    )
    res = auth_api.post("/api/v1/guide-bookings/", _guide_booking_payload(guide, point.pk), format="json")
    assert res.status_code == 201, res.data
    assert res.data["meeting_point"] == "Registon, Registon maydoni"
    assert res.data["meeting_latitude"] == "39.654167"
    b = GuideBooking.objects.get()
    assert b.meeting_place == point


def test_other_guides_or_inactive_point_rejected(auth_api, guide, samarqand):
    other_user = User.objects.create_user(email="g2@example.com", password=PASSWORD)
    other = GuideProfile.objects.create(
        user=other_user,
        slug="boshqa",
        display_name="B",
        phone="+998901112244",
        languages=["en"],
        price_half_day_uzs=1,
        price_full_day_uzs=1,
        price_per_day_uzs=1,
        status=GuideProfile.Status.APPROVED,
    )
    fields = {k: v for k, v in POINT.items() if k != "destination"}
    foreign = GuideMeetingPoint.objects.create(guide=other, destination=samarqand, **fields)
    res = auth_api.post("/api/v1/guide-bookings/", _guide_booking_payload(guide, foreign.pk), format="json")
    assert res.status_code == 400
    inactive = GuideMeetingPoint.objects.create(guide=guide, destination=samarqand, is_active=False, **fields)
    res = auth_api.post("/api/v1/guide-bookings/", _guide_booking_payload(guide, inactive.pk), format="json")
    assert res.status_code == 400


def test_used_meeting_point_is_deactivated_not_deleted(guide_api, guide, user, samarqand):
    fields = {k: v for k, v in POINT.items() if k != "destination"}
    point = GuideMeetingPoint.objects.create(guide=guide, destination=samarqand, **fields)
    guide_services.request_booking(
        user=user,
        guide=guide,
        destination=samarqand,
        duration="full_day",
        start_date=timezone.localdate() + timedelta(days=10),
        start_time=time(9),
        days=1,
        group_size=1,
        language="en",
        meeting_point=point,
        contact_name="A",
        contact_phone="+998900000000",
    )
    assert guide_api.delete(f"/api/v1/cabinet/guide/meeting-points/{point.pk}/").status_code == 204
    point.refresh_from_db()
    assert point.is_active is False
    assert GuideBooking.objects.get().meeting_point == "Registon, Registon maydoni"


def test_tour_meeting_point_required(agency_api, category, samarqand):
    payload = {
        "title": "Yangi tur",
        "destination": "samarqand",
        "categories": [category.slug],
        "price_uzs": 100000,
        "cancellation_policy": "free",
    }
    res = agency_api.post("/api/v1/cabinet/tours/", payload, format="json")
    assert res.status_code == 400
    assert "meeting_point" in res.data
    res = agency_api.post("/api/v1/cabinet/tours/", {**payload, "meeting_point": "   "}, format="json")
    assert res.status_code == 400


def test_tour_submit_requires_meeting_location(agency_api, tour, settings, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.tours.models import TourMedia

    settings.MEDIA_ROOT = tmp_path
    gif = (
        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )
    TourMedia.objects.create(tour=tour, file=SimpleUploadedFile("a.gif", gif, content_type="image/gif"))
    tour.status = "draft"
    tour.meeting_latitude = tour.meeting_longitude = None
    tour.meeting_map_url = ""
    tour.save()
    res = agency_api.post(f"/api/v1/cabinet/tours/{tour.slug}/submit/")
    assert res.status_code == 400
    assert "meeting_map_url" in res.data
    tour.meeting_map_url = "https://yandex.uz/maps/?pt=66.95,39.65"
    tour.save()
    assert agency_api.post(f"/api/v1/cabinet/tours/{tour.slug}/submit/").status_code == 200


# ---------- 3. Turistga keladigan xabarlarda bron kodi yo'q ----------


def test_tourist_messages_have_no_booking_code(user, departure):
    from apps.bookings.services import cancel_booking, confirm_booking, create_booking

    user.phone, user.phone_verified = "+998901234567", True
    user.save()
    b = create_booking(
        user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="+998901234567"
    )
    confirm_booking(b)
    cancel_booking(b, by="agency", reason="Ob-havo")
    tourist_msgs = UserMessage.objects.filter(recipient__in=[user.email, user.phone])
    assert tourist_msgs.count() >= 3
    for m in tourist_msgs:
        assert b.code not in m.body and b.code not in m.subject
    for m in mail.outbox:
        assert b.code not in m.subject and b.code not in m.body


# ---------- 5. Google orqali kirish ----------


def _info(**kw):
    data = {
        "aud": "cid.apps.googleusercontent.com",
        "iss": "https://accounts.google.com",
        "exp": str(int(timezone.now().timestamp()) + 600),
        "sub": "google-123",
        "email": "Ali@Gmail.com",
        "email_verified": "true",
        "given_name": "Ali",
        "family_name": "Valiyev",
    }
    data.update(kw)
    return data


@pytest.fixture
def google_on(settings):
    settings.GOOGLE_CLIENT_ID = "cid.apps.googleusercontent.com"


def _google(api, info):
    with mock.patch.object(google, "fetch_token_info", return_value=info):
        return api.post("/api/v1/auth/google/", {"credential": "id-token"}, format="json")


def test_google_disabled_by_default(api):
    res = api.post("/api/v1/auth/google/", {"credential": "x"}, format="json")
    assert res.status_code == 503


def test_google_creates_user(api, google_on):
    res = _google(api, _info())
    assert res.status_code == 200, res.data
    assert res.data["is_new"] is True
    assert res.data["access"] and res.data["refresh"]
    u = User.objects.get(email="ali@gmail.com")
    assert (u.google_sub, u.email_verified, u.first_name, u.has_usable_password()) == (
        "google-123",
        True,
        "Ali",
        False,
    )
    res = _google(api, _info())
    assert res.data["is_new"] is False
    assert User.objects.count() == 1


@pytest.mark.parametrize(
    "bad",
    [
        {"aud": "boshqa-client"},
        {"iss": "evil.com"},
        {"email_verified": "false"},
        {"exp": "1"},
        {"sub": ""},
    ],
)
def test_google_bad_token(api, google_on, bad):
    assert _google(api, _info(**bad)).status_code == 400
    assert not User.objects.filter(email="ali@gmail.com").exists()


def test_google_links_existing_verified_account(api, google_on, user):
    user.email_verified = True
    user.save()
    res = _google(api, _info(email=user.email))
    assert res.status_code == 200
    user.refresh_from_db()
    assert user.google_sub == "google-123"
    assert user.check_password(PASSWORD)  # tasdiqlangan akkaunt paroli saqlanadi


def test_google_takes_over_unverified_squatted_account(api, google_on, user):
    """Kimdir boshqa odamning emailida (tasdiqlamasdan) akkaunt ochgan bo'lsa — uning paroli bekor bo'ladi."""
    assert user.email_verified is False
    res = _google(api, _info(email=user.email))
    assert res.status_code == 200
    user.refresh_from_db()
    assert user.email_verified is True
    assert not user.has_usable_password()


def test_google_blocked_user(api, google_on, user):
    user.is_active = False
    user.email_verified = True
    user.save()
    assert _google(api, _info(email=user.email)).status_code == 400


def test_google_features_flag(api, google_on):
    assert api.get("/api/v1/features/").data["google_login"] == {
        "enabled": True,
        "client_id": "cid.apps.googleusercontent.com",
    }


def test_phone_token_is_signed():
    assert signing.loads(phone_token("+998901234567"), salt=TOKEN_SALT) == {"p": "+998901234567"}
