"""Moderatsiya: saytga yuklanadigan hamma narsa admin tasdig'idan keyin chiqadi.

- Hamkor tasdiqlangan ma'lumotini o'zgartirsa — qayta tekshiruvga, tasdiqlanguncha saytdan yashirin.
- Admin qaytarsa — izoh hamkorga boradi (email/Telegram), kabinetda ham ko'rinadi.
- Admin hamkor ma'lumotlarini O'ZGARTIRA OLMAYDI — faqat tasdiqlaydi yoki qaytaradi.
- Sharhlar ham admin tasdiqlagach chiqadi.
"""

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from rest_framework.test import APIClient

from apps.agencies import services as agency_services
from apps.agencies.models import Agency
from apps.guides.models import GuideProfile
from apps.hotels import services as hotel_services
from apps.hotels.models import Hotel
from apps.notifications.models import UserMessage
from apps.tours.models import Tour

from .media_samples import PNG
from .test_guides import guide, guide_api, guide_user  # noqa: F401 — fixture'lar
from .test_hotels import hotel, owner, owner_api  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    c.force_login(admin_user)
    return c


def messages_text() -> str:
    return "\n".join(UserMessage.objects.values_list("body", flat=True))


# ---------- Mehmonxona ----------


def test_hotel_edit_goes_back_to_review_and_hides(owner_api, hotel):  # noqa: F811
    public = APIClient()
    assert public.get("/api/v1/hotels/registon-plaza/").status_code == 200
    res = owner_api.patch("/api/v1/hotels/me/", {"description": "Yangi tavsif"}, format="json")
    assert res.status_code == 200, res.data
    hotel.refresh_from_db()
    assert hotel.status == Hotel.Status.PENDING
    assert public.get("/api/v1/hotels/registon-plaza/").status_code == 404  # tasdiqlanguncha yashirin

    hotel_services.approve_hotel(hotel)
    assert public.get("/api/v1/hotels/registon-plaza/").status_code == 200


def test_hotel_new_photo_goes_to_review(owner_api, hotel):  # noqa: F811
    res = owner_api.post(
        "/api/v1/cabinet/hotel/images/", {"image": SimpleUploadedFile("a.png", PNG)}, format="multipart"
    )
    assert res.status_code == 201, res.data
    hotel.refresh_from_db()
    assert hotel.status == Hotel.Status.PENDING


def test_admin_returns_hotel_with_note(admin_client, hotel, owner):  # noqa: F811
    url = "/control/admin/hotels/hotel/"
    data = {"action": "return_to_owner", ACTION_CHECKBOX_NAME: [hotel.pk]}
    res = admin_client.post(url, data)
    assert res.status_code == 200 and "Kamchiliklar" in res.content.decode()  # izoh so'raladi
    res = admin_client.post(url, {**data, "apply": "1", "note": "Rasmlar xira, narxlar yo'q"})
    assert res.status_code == 302
    hotel.refresh_from_db()
    assert hotel.status == Hotel.Status.REJECTED
    assert hotel.moderation_note == "Rasmlar xira, narxlar yo'q"
    assert "Rasmlar xira, narxlar yo'q" in messages_text()  # hamkorga xabar ketdi


def test_admin_cannot_edit_hotel_data(admin_client, hotel):  # noqa: F811
    page = admin_client.get(f"/control/admin/hotels/hotel/{hotel.pk}/change/").content.decode()
    assert 'name="name"' not in page  # nomi — faqat o'qish uchun
    assert 'name="commission_percent"' in page  # platforma sozlamasi — tahrirlanadi
    admin_client.post(
        f"/control/admin/hotels/hotel/{hotel.pk}/change/",
        {"name": "Admin o'zgartirdi", "commission_percent": "12", "_save": "1"},
    )
    hotel.refresh_from_db()
    assert hotel.name == "Registon Plaza"
    assert admin_client.get("/control/admin/hotels/hotel/add/").status_code == 403
    assert admin_client.get("/control/admin/hotels/roomtype/").status_code in (
        403,
        404,
    )  # alohida bo'lim yo'q


# ---------- Gid ----------


def test_guide_edit_goes_back_to_review(guide_api, guide):  # noqa: F811
    assert APIClient().get("/api/v1/guides/aziz/").status_code == 200
    res = guide_api.patch("/api/v1/guides/me/", {"languages": ["uz", "en", "de", "fr"]}, format="json")
    assert res.status_code == 200, res.data
    guide.refresh_from_db()
    assert guide.status == GuideProfile.Status.PENDING
    assert APIClient().get("/api/v1/guides/aziz/").status_code == 404


def test_admin_cannot_edit_guide_languages(admin_client, guide):  # noqa: F811
    admin_client.post(
        f"/control/admin/guides/guideprofile/{guide.pk}/change/",
        {"languages": '["uz"]', "display_name": "X", "commission_percent": "10", "_save": "1"},
    )
    guide.refresh_from_db()
    assert guide.languages == ["uz", "en", "de"] and guide.display_name == "Aziz"


# ---------- Tur va agentlik ----------


def test_published_tour_edit_goes_back_to_review(agency_api, tour):
    assert APIClient().get(f"/api/v1/tours/{tour.slug}/").status_code == 200
    res = agency_api.patch(f"/api/v1/cabinet/tours/{tour.slug}/", {"price_uzs": 990_000}, format="json")
    assert res.status_code == 200, res.data
    tour.refresh_from_db()
    assert tour.status == Tour.Status.PENDING_REVIEW
    assert APIClient().get(f"/api/v1/tours/{tour.slug}/").status_code == 404


def test_tour_new_media_goes_back_to_review(agency_api, tour):
    url = f"/api/v1/cabinet/tours/{tour.slug}/media/"
    assert (
        agency_api.post(url, {"file": SimpleUploadedFile("a.png", PNG)}, format="multipart").status_code
        == 201
    )
    tour.refresh_from_db()
    assert tour.status == Tour.Status.PENDING_REVIEW


def test_admin_returns_tour_with_note(admin_client, tour, agency_user):
    tour.status = Tour.Status.PENDING_REVIEW
    tour.save()
    res = admin_client.post(
        "/control/admin/tours/tour/",
        {
            "action": "return_to_agency",
            ACTION_CHECKBOX_NAME: [tour.pk],
            "apply": "1",
            "note": "Dastur to'liq emas",
        },
    )
    assert res.status_code == 302
    tour.refresh_from_db()
    assert (tour.status, tour.moderation_note) == (Tour.Status.REJECTED, "Dastur to'liq emas")
    assert "Dastur to'liq emas" in messages_text()


def test_agency_profile_edit_hides_agency_until_approved(agency_api, agency, tour):
    assert APIClient().get(f"/api/v1/agencies/{agency.slug}/").status_code == 200
    res = agency_api.patch("/api/v1/cabinet/agency/", {"description": "Yangi tavsif"}, format="json")
    assert res.status_code == 200, res.data
    agency.refresh_from_db()
    assert agency.moderation_status == Agency.Moderation.PENDING
    assert APIClient().get(f"/api/v1/agencies/{agency.slug}/").status_code == 404
    assert APIClient().get(f"/api/v1/tours/{tour.slug}/").status_code == 404  # turlari ham
    assert agency_api.get("/api/v1/cabinet/tours/").status_code == 200  # kabinet ishlayveradi

    agency_services.return_agency(agency, "Logotip yo'q")
    assert "Logotip yo'q" in messages_text()
    agency_services.approve_agency(agency)
    assert APIClient().get(f"/api/v1/agencies/{agency.slug}/").status_code == 200


def test_admin_cannot_add_or_delete_partner_data(admin_client, agency, tour):
    assert admin_client.get("/control/admin/agencies/agency/add/").status_code == 403
    assert admin_client.get("/control/admin/tours/tour/add/").status_code == 403
    assert admin_client.get(f"/control/admin/tours/tour/{tour.pk}/delete/").status_code == 403
    admin_client.post(f"/control/admin/tours/tour/{tour.pk}/change/", {"title": "Boshqa", "_save": "1"})
    tour.refresh_from_db()
    assert tour.title == "Samarqand 1 kun"


def test_partner_gets_telegram_message_with_note(owner, hotel, settings):  # noqa: F811
    settings.TELEGRAM_BOT_TOKEN = "123:TEST"
    owner.telegram_id = 777
    owner.save()
    hotel_services.reject_hotel(hotel, "Manzil noto'g'ri")
    msg = UserMessage.objects.get(channel=UserMessage.Channel.TELEGRAM)
    assert msg.recipient == "777" and "Manzil noto'g'ri" in msg.body


# ---------- Admin dashboard ----------


def test_admin_dashboard_shows_queue_money_and_actions(admin_client, hotel, tour, owner):  # noqa: F811
    from apps.bookings.models import Booking

    hotel.status = Hotel.Status.PENDING
    hotel.save()
    tour.status = Tour.Status.PENDING_REVIEW
    tour.save()

    page = admin_client.get("/control/admin/").content.decode()
    assert "Tekshiruv navbati" in page and "komissiya" in page
    assert "2 ta</b> narsa tasdiqlashingizni kutyapti" in page
    assert "/control/admin/hotels/hotel/?status__exact=pending" in page
    assert "/control/admin/tours/tour/?status__exact=pending_review" in page
    assert Booking.objects.count() == 0  # bo'sh bazada ham sahifa ochiladi

    # qaytarish amali "Oxirgi admin amallari" da ko'rinadi
    admin_client.post(
        "/control/admin/hotels/hotel/",
        {"action": "return_to_owner", ACTION_CHECKBOX_NAME: [hotel.pk], "apply": "1", "note": "Telefon yo'q"},
    )
    page = admin_client.get("/control/admin/").content.decode()
    assert "Qaytarildi: Telefon yo&#x27;q" in page
    assert "1 ta</b> narsa" in page  # mehmonxona endi navbatda emas, faqat tur qoldi


def test_dashboard_requires_staff(client, user):
    assert client.get("/control/admin/").status_code == 302  # login sahifasiga
    client.force_login(user)
    assert client.get("/control/admin/").status_code == 302  # oddiy foydalanuvchi kira olmaydi


# ---------- Hamkor kabineti ----------


def test_guide_sees_own_reviews_and_replies(guide_api, guide, user, samarqand):  # noqa: F811
    from apps.guides.models import GuideBooking, GuideReview

    from .test_guides import confirmed

    b = confirmed(user, guide, samarqand)
    GuideBooking.objects.filter(pk=b.pk).update(status="completed")
    r = GuideReview.objects.create(booking=b, user=user, guide=guide, rating=5, text="Zo'r")
    rows = guide_api.get("/api/v1/cabinet/guide/reviews/").data["results"]
    assert [x["id"] for x in rows] == [r.pk]  # tekshiruvdagisi ham ko'rinadi
    res = guide_api.post(f"/api/v1/cabinet/guide/reviews/{r.pk}/reply/", {"text": "Rahmat!"}, format="json")
    assert res.status_code == 200 and res.data["guide_reply"] == "Rahmat!"


def test_regular_user_has_no_cabinet_access(auth_api):
    for path in ("/api/v1/cabinet/agency/", "/api/v1/cabinet/guide/reviews/", "/api/v1/cabinet/hotel/rooms/"):
        assert auth_api.get(path).status_code in (403, 404), path


def test_me_shows_is_staff(auth_api, admin_user):
    assert auth_api.get("/api/v1/auth/me/").data["is_staff"] is False
    c = APIClient()
    c.force_authenticate(admin_user)
    assert c.get("/api/v1/auth/me/").data["is_staff"] is True


# ---------- Admin hisobi (Render: Environment'dan) ----------


def test_ensure_admin_creates_or_promotes(monkeypatch, db):
    from django.core.management import call_command

    from apps.accounts.models import User

    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "Boss@Gmail.com")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "Kuchli-Parol-2026")
    # oldin Google orqali oddiy foydalanuvchi bo'lib kirgan
    User.objects.create_user(email="boss@gmail.com", first_name="Boss")
    call_command("ensure_admin")
    u = User.objects.get(email__iexact="boss@gmail.com")
    assert u.is_staff and u.is_superuser and u.check_password("Kuchli-Parol-2026")
    assert User.objects.count() == 1

    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "Yangi-Parol-2027")  # parolni almashtirish
    call_command("ensure_admin")
    u.refresh_from_db()
    assert u.check_password("Yangi-Parol-2027")

    c = Client()
    assert c.login(email="boss@gmail.com", password="Yangi-Parol-2027")
    assert c.get("/control/admin/").status_code == 200


def test_ensure_admin_creates_new(monkeypatch, db):
    from django.core.management import call_command

    from apps.accounts.models import User

    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "admin@meyzi.uz")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "Kuchli-Parol-2026")
    call_command("ensure_admin")
    assert User.objects.get(email="admin@meyzi.uz").is_superuser
