"""Saytdagi admin paneli (/control) API: faqat adminlar; ko'rish, tasdiqlash, izoh bilan qaytarish."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel
from apps.notifications.models import UserMessage
from apps.tours.models import Tour

from .conftest import PASSWORD
from .media_samples import PDF
from .test_guides import guide, guide_user  # noqa: F401 — fixture'lar
from .test_hotels import hotel, owner  # noqa: F401
from .test_reviews import completed  # noqa: F401

pytestmark = pytest.mark.django_db
C = "/api/v1/control/"


@pytest.fixture(autouse=True)
def dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def test_login_only_for_staff(admin_user, user):
    api = APIClient()
    res = api.post(C + "login/", {"email": "ADMIN@example.com", "password": PASSWORD}, format="json")
    assert res.status_code == 200 and res.data["access"] and res.data["user"]["is_staff"] is True
    # to'g'ri parolli oddiy foydalanuvchi ham kira olmaydi — xato bir xil
    res = api.post(C + "login/", {"email": user.email, "password": PASSWORD}, format="json")
    assert res.status_code == 400 and res.data["detail"] == "Email yoki parol noto'g'ri."
    res = api.post(C + "login/", {"email": "admin@example.com", "password": "xato"}, format="json")
    assert res.status_code == 400 and res.data["detail"] == "Email yoki parol noto'g'ri."


def test_regular_user_gets_403(auth_api):
    assert auth_api.get(C + "dashboard/").status_code == 403
    assert auth_api.get(C + "items/hotel/").status_code == 403
    assert APIClient().get(C + "dashboard/").status_code == 401


def test_old_admin_url_is_gone(client):
    assert client.get("/admin/").status_code == 404
    assert client.get("/control/admin/").status_code == 302  # login sahifasiga


def test_dashboard_queue_and_list(staff_api, hotel, tour):  # noqa: F811
    hotel.status = Hotel.Status.PENDING
    hotel.save()
    data = staff_api.get(C + "dashboard/").data
    q = {i["kind"]: i for i in data["queue"]}
    # yangi ariza avval moderatorda: adminning "tasdiqlash kerak" navbatida emas, "moderatorda" sonida
    assert q["hotel"]["count"] == 0 and q["hotel"]["with_moderator"] == 1 and q["tour"]["count"] == 0
    assert {"today", "week", "month", "chart"} <= set(data["money"])

    rows = staff_api.get(C + "items/hotel/?state=precheck").data
    assert [r["title"] for r in rows["results"]] == ["Registon Plaza"]
    assert rows["counts"]["precheck"] == 1 and rows["counts"]["pending"] == 0
    assert staff_api.get(C + "items/hotel/?state=approved").data["results"] == []
    assert staff_api.get(C + "items/nima/").status_code == 404


def test_hotel_detail_and_return_with_note(staff_api, hotel, owner):  # noqa: F811
    hotel.status = Hotel.Status.PENDING
    hotel.save()
    d = staff_api.get(C + f"items/hotel/{hotel.pk}/").data
    assert d["name"] == "Registon Plaza" and d["state"] == "precheck"
    assert {"approve", "precheck", "return"} <= set(
        d["actions"]
    )  # admin moderatorni kutmasdan ham hal qila oladi
    assert {"media", "rooms", "members"} <= set(d["data"])

    url = C + f"items/hotel/{hotel.pk}/return/"
    assert staff_api.post(url, {"note": ""}, format="json").status_code == 400  # izoh majburiy
    res = staff_api.post(url, {"note": "Rasmlar xira, narx yo'q"}, format="json")
    assert res.status_code == 200 and res.data["state"] == "rejected"
    hotel.refresh_from_db()
    assert hotel.moderation_note == "Rasmlar xira, narx yo'q"
    assert UserMessage.objects.filter(body__contains="Rasmlar xira").exists()
    # tarixda ko'rinadi
    history = staff_api.get(C + f"items/hotel/{hotel.pk}/").data["history"]
    assert "Qaytarildi: Rasmlar xira" in history[0]["message"]

    res = staff_api.post(C + f"items/hotel/{hotel.pk}/approve/", format="json")
    assert res.data["state"] == "approved"
    assert APIClient().get("/api/v1/hotels/registon-plaza/").status_code == 200


def test_tour_approve_and_suspend_rules(staff_api, tour):
    tour.status = Tour.Status.PENDING_REVIEW
    tour.save()
    assert staff_api.post(C + f"items/tour/{tour.pk}/approve/").data["state"] == "approved"
    tour.refresh_from_db()
    assert tour.status == "published"
    assert staff_api.post(C + f"items/tour/{tour.pk}/suspend/").status_code == 403  # turga qo'llanmaydi


def test_guide_suspend_activate_and_certificate(staff_api, guide):  # noqa: F811
    guide.certificate_file.save("s.pdf", SimpleUploadedFile("s.pdf", PDF))
    d = staff_api.get(C + f"items/guide/{guide.pk}/").data
    assert d["data"]["certificate_url"] == f"/control/items/guide/{guide.pk}/certificate"
    res = staff_api.get(C + f"items/guide/{guide.pk}/certificate/")
    assert res.status_code == 200 and b"".join(res.streaming_content) == PDF
    assert APIClient().get(C + f"items/guide/{guide.pk}/certificate/").status_code == 401

    assert staff_api.post(C + f"items/guide/{guide.pk}/suspend/").data["state"] == "suspended"
    assert staff_api.post(C + f"items/guide/{guide.pk}/activate/").data["state"] == "approved"
    guide.refresh_from_db()
    assert guide.status == GuideProfile.Status.APPROVED


def test_agency_application_approve(staff_api, user):
    from apps.agencies.models import Agency, AgencyApplication

    app = AgencyApplication.objects.create(
        agency_name="Yangi Tur", contact_person="Ali", phone="+998901234567", user=user
    )
    assert staff_api.get(C + "items/application/").data["counts"]["pending"] == 1
    res = staff_api.post(C + f"items/application/{app.pk}/approve/")
    assert res.status_code == 200 and res.data["state"] == "approved"
    assert Agency.objects.filter(name="Yangi Tur", members__user=user).exists()


def test_review_publish_and_hide(staff_api, user, tour, completed):  # noqa: F811
    from apps.reviews.models import Review

    b = completed(user)
    r = Review.objects.create(booking=b, user=user, tour=tour, agency=tour.agency, rating=5, text="Zo'r")
    assert staff_api.get(C + "items/review/").data["counts"]["pending"] == 1
    assert staff_api.post(C + f"items/review/{r.pk}/approve/").data["state"] == "approved"
    assert (
        staff_api.post(C + f"items/review/{r.pk}/return/", {"note": ""}, format="json").data["state"]
        == "rejected"
    )
