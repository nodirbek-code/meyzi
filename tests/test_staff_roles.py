"""Ishchilar (soha moderatorlari): faqat o'z sohasi; moderator tekshiradi → admin yakuniy tasdiqlaydi."""

import pytest
from django.test import Client
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.guides.models import GuideProfile
from apps.hotels import services as hotel_services
from apps.hotels.models import Hotel
from apps.notifications.models import UserMessage

from .conftest import PASSWORD
from .test_guides import guide, guide_user  # noqa: F401 — fixture'lar
from .test_hotels import hotel, owner, owner_api  # noqa: F401

pytestmark = pytest.mark.django_db
C = "/api/v1/control/"


def staff(area: str, **kw) -> APIClient:
    u = User.objects.create_user(
        email=f"{area}@meyzi.uz", password=PASSWORD, is_staff=True, staff_area=area, **kw
    )
    c = APIClient()
    c.force_authenticate(u)
    c.user = u
    return c


@pytest.fixture
def hotel_mod(db):
    return staff("hotels")


@pytest.fixture
def admin_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


@pytest.fixture
def pending_hotel(hotel):  # noqa: F811
    hotel.status = Hotel.Status.PENDING
    hotel.save()
    return hotel


def test_moderator_sees_only_own_area(hotel_mod, guide):  # noqa: F811
    me = hotel_mod.get(C + "me/").data
    assert me["role"] == "hotels" and set(me["kinds"]) == {"hotel", "hotel_review"}
    dash = hotel_mod.get(C + "dashboard/").data
    assert dash["money"] is None and dash["platform"] == []  # pul va platforma — faqat asosiy admin
    assert {q["kind"] for q in dash["queue"]} == {"hotel", "hotel_review"}
    assert hotel_mod.get(C + "items/guide/").status_code == 404
    assert hotel_mod.get(C + f"items/guide/{guide.pk}/").status_code == 404
    assert hotel_mod.get(C + "items/tour/").status_code == 404
    assert hotel_mod.get(C + "manage/").status_code == 403  # Boshqarish — faqat admin


def test_moderator_cannot_open_django_admin(db):
    User.objects.create_user(email="m@meyzi.uz", password=PASSWORD, is_staff=True, staff_area="guides")
    c = Client()
    c.login(email="m@meyzi.uz", password=PASSWORD)
    assert c.get("/control/admin/").status_code == 302  # login sahifasiga — kirish yo'q


def test_moderator_can_log_in_to_control(db):
    User.objects.create_user(email="m2@meyzi.uz", password=PASSWORD, is_staff=True, staff_area="hotels")
    res = APIClient().post(C + "login/", {"email": "m2@meyzi.uz", "password": PASSWORD}, format="json")
    assert res.status_code == 200 and res.data["user"]["staff_area"] == "hotels"


def test_two_stage_flow_moderator_then_admin(hotel_mod, admin_api, pending_hotel):
    h = pending_hotel
    item = hotel_mod.get(C + f"items/hotel/{h.pk}/").data
    assert item["state"] == "precheck" and item["actions"] == ["precheck", "return"]
    assert hotel_mod.post(C + f"items/hotel/{h.pk}/approve/").status_code == 403  # yakuniy tasdiq — admin

    # adminda hali "tasdiqlash kerak" emas
    q = {i["kind"]: i for i in admin_api.get(C + "dashboard/").data["queue"]}
    assert q["hotel"]["count"] == 0 and q["hotel"]["with_moderator"] == 1

    res = hotel_mod.post(
        C + f"items/hotel/{h.pk}/precheck/", {"note": "Hujjatlar to'liq, rasmlar yaxshi"}, format="json"
    )
    assert res.status_code == 200 and res.data["state"] == "pending"
    h.refresh_from_db()
    assert h.status == "pending" and h.prechecked_by == hotel_mod.user and h.prechecked_at
    assert hotel_mod.get(C + f"items/hotel/{h.pk}/").data["actions"] == []  # endi adminda

    q = {i["kind"]: i for i in admin_api.get(C + "dashboard/").data["queue"]}
    assert q["hotel"]["count"] == 1  # admin navbatida
    item = admin_api.get(C + f"items/hotel/{h.pk}/").data
    assert item["precheck"]["note"] == "Hujjatlar to'liq, rasmlar yaxshi"
    assert "approve" in item["actions"]
    assert admin_api.post(C + f"items/hotel/{h.pk}/approve/").data["state"] == "approved"


def test_moderator_returns_to_partner(hotel_mod, pending_hotel):
    h = pending_hotel
    assert hotel_mod.post(C + f"items/hotel/{h.pk}/return/", {"note": ""}, format="json").status_code == 400
    res = hotel_mod.post(
        C + f"items/hotel/{h.pk}/return/", {"note": "Manzil noto'g'ri yozilgan"}, format="json"
    )
    assert res.status_code == 200 and res.data["state"] == "rejected"
    h.refresh_from_db()
    assert h.moderation_note == "Manzil noto'g'ri yozilgan"


def test_partner_edit_after_precheck_goes_back_to_moderator(hotel_mod, owner_api, pending_hotel):  # noqa: F811
    h = pending_hotel
    hotel_mod.post(C + f"items/hotel/{h.pk}/precheck/", format="json")
    owner_api.patch("/api/v1/hotels/me/", {"description": "Yangi tavsif"}, format="json")
    h.refresh_from_db()
    assert h.prechecked_at is None  # yana moderatorga


def test_admin_return_resets_precheck(hotel_mod, admin_api, pending_hotel):
    h = pending_hotel
    hotel_mod.post(C + f"items/hotel/{h.pk}/precheck/", format="json")
    admin_api.post(
        C + f"items/hotel/{h.pk}/return/", {"note": "Narxlar juda yuqori ko'rsatilgan"}, format="json"
    )
    h.refresh_from_db()
    assert h.status == "rejected" and h.prechecked_at is None


def test_guide_moderator(guide):  # noqa: F811
    mod = staff("guides")
    guide.status = GuideProfile.Status.PENDING
    guide.save()
    assert mod.get(C + "items/hotel/").status_code == 404
    assert mod.post(C + f"items/guide/{guide.pk}/precheck/").data["state"] == "pending"
    assert mod.post(C + f"items/guide/{guide.pk}/suspend/").status_code == 403


def test_new_hotel_application_notifies_hotel_moderator(settings, owner, samarqand):  # noqa: F811
    settings.TELEGRAM_BOT_TOKEN = "123:TEST"
    User.objects.create_user(email="hm@meyzi.uz", is_staff=True, staff_area="hotels", telegram_id=4242)
    User.objects.create_user(email="gm@meyzi.uz", is_staff=True, staff_area="guides", telegram_id=5353)
    hotel_services.register_hotel(
        user=owner, name="Yangi", destination=samarqand, address="x", phone="+998901112233"
    )
    recipients = set(UserMessage.objects.filter(channel="telegram").values_list("recipient", flat=True))
    assert recipients == {"4242"}  # faqat mehmonxona moderatoriga
