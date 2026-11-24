"""/control → Boshqarish: admin yaratadi/tahrirlaydi; hamkor o'zi kiritgan ma'lumot — faqat moderatsiya."""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.catalog.models import Destination
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel, HotelImage
from apps.tours.models import Tour

from .media_samples import MP4, PNG
from .test_hotels import hotel, owner  # noqa: F401 — fixture'lar

pytestmark = pytest.mark.django_db
M = "/api/v1/control/manage/"


@pytest.fixture(autouse=True)
def dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def test_every_section_opens_with_schema(staff_api, samarqand, tour):
    index = staff_api.get(M).data
    keys = {r["key"] for r in index}
    assert {
        "destination",
        "place",
        "tour_category",
        "article",
        "faq",
        "page",
        "agency",
        "hotel",
        "room_type",
        "hotel_media",
        "guide",
        "meeting_point",
        "tour",
        "tour_media",
        "departure",
        "user",
    } <= keys
    for key in keys:
        res = staff_api.get(M + f"{key}/")
        assert res.status_code == 200, (key, res.data)
        assert res.data["schema"], key


def test_regular_user_forbidden(auth_api):
    assert auth_api.get(M).status_code == 403
    assert auth_api.post(M + "faq/", {"question": "Q?", "answer": "A"}, format="json").status_code == 403


def test_destination_crud_with_auto_slug(staff_api):
    res = staff_api.post(M + "destination/", {"name": "Xiva Shahri", "is_published": True}, format="json")
    assert res.status_code == 201, res.data
    d = Destination.objects.get(pk=res.data["id"])
    assert d.slug == "xiva-shahri"
    assert staff_api.patch(M + f"destination/{d.pk}/", {"region": "Xorazm"}, format="json").status_code == 200
    d.refresh_from_db()
    assert d.region == "Xorazm" and d.slug == "xiva-shahri"
    assert staff_api.delete(M + f"destination/{d.pk}/").status_code == 204


def test_faq_validation_errors(staff_api):
    res = staff_api.post(M + "faq/", {"question": ""}, format="json")
    assert res.status_code == 400 and {"question", "answer"} <= set(res.data)


def test_admin_creates_agency_with_owner_and_platform_tour(staff_api, samarqand, category):
    res = staff_api.post(M + "agency/", {"name": "Yangi Yo'l", "owner_email": "Ega@Gmail.com"}, format="json")
    assert res.status_code == 201, res.data
    a = Agency.objects.get(pk=res.data["id"])
    assert a.managed_by_platform and a.moderation_status == "approved"
    ega = User.objects.get(email="ega@gmail.com")
    assert a.members.filter(user=ega).exists() and ega.role == "agency"

    data = {
        "agency": a.pk,
        "destination": samarqand.pk,
        "title": "Admin turi",
        "categories": [category.pk],
        "duration_days": 1,
        "duration_nights": 0,
        "max_group_size": 10,
        "meeting_point": "Registon",
        "price_uzs": 500000,
        "cancellation_policy": "free",
        "included": ["Transport"],
        "status": "published",
    }
    res = staff_api.post(M + "tour/", data, format="json")
    assert res.status_code == 201, res.data
    t = Tour.objects.get(pk=res.data["id"])
    assert (
        t.status == "published" and t.published_at and t.included == ["Transport"] and t.slug == "admin-turi"
    )


def test_partner_data_is_read_only_for_admin(staff_api, hotel, tour):  # noqa: F811
    # hamkorning o'zi yaratgan mehmonxona va agentlik turi
    rows = staff_api.get(M + "hotel/").data["results"]
    row = next(r for r in rows if r["id"] == hotel.pk)
    assert row["editable"] is False and row["moderation_url"] == f"/control/queue/hotel/{hotel.pk}"
    res = staff_api.patch(M + f"hotel/{hotel.pk}/", {"name": "Admin o'zgartirdi"}, format="json")
    assert res.status_code == 403
    assert (
        staff_api.patch(M + f"tour/{tour.pk}/", {"title": "X"}, format="json").status_code == 403
    )  # hamkor turi — admin o'zgartira olmaydi
    hotel.refresh_from_db()
    assert hotel.name == "Registon Plaza"
    # hamkor mehmonxonasiga xona qo'shib bo'lmaydi
    res = staff_api.post(
        M + "room_type/",
        {"hotel": hotel.pk, "name": "X", "capacity": 2, "price_per_night_uzs": 1, "total_rooms": 1},
        format="json",
    )
    assert res.status_code == 400 and "hotel" in res.data


def test_admin_hotel_rooms_and_media(staff_api, samarqand):
    res = staff_api.post(
        M + "hotel/",
        {
            "name": "Platforma Mehmonxonasi",
            "destination": samarqand.pk,
            "address": "Samarqand",
            "phone": "+998901112233",
            "check_in_time": "14:00",
            "check_out_time": "12:00",
            "amenities": ["wifi"],
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    h = Hotel.objects.get(pk=res.data["id"])
    assert h.status == "approved" and h.managed_by_platform

    res = staff_api.post(
        M + "room_type/",
        {"hotel": h.pk, "name": "Lyuks", "capacity": 2, "price_per_night_uzs": 900000, "total_rooms": 3},
        format="json",
    )
    assert res.status_code == 201, res.data

    res = staff_api.post(
        M + "hotel_media/",
        {"hotel": h.pk, "image": SimpleUploadedFile("a.png", PNG), "is_cover": "true"},
        format="multipart",
    )
    assert res.status_code == 201, res.data
    res = staff_api.post(
        M + "hotel_media/", {"hotel": h.pk, "image": SimpleUploadedFile("v.mp4", MP4)}, format="multipart"
    )
    assert res.status_code == 201 and HotelImage.objects.get(pk=res.data["id"]).kind == "video"
    res = staff_api.post(
        M + "hotel_media/",
        {"hotel": h.pk, "image": SimpleUploadedFile("x.png", b"not image")},
        format="multipart",
    )
    assert res.status_code == 400


def test_admin_creates_guide_needs_account_email(staff_api, samarqand):
    data = {
        "display_name": "Platforma Gidi",
        "phone": "+998901234567",
        "languages": json.dumps(["uz", "en"]),
        "destinations": [samarqand.pk],
        "price_half_day_uzs": 1,
        "price_full_day_uzs": 2,
        "price_per_day_uzs": 2,
    }
    assert staff_api.post(M + "guide/", data, format="multipart").status_code == 400  # email shart
    res = staff_api.post(M + "guide/", {**data, "owner_email": "gid@meyzi.uz"}, format="multipart")
    assert res.status_code == 201, res.data
    g = GuideProfile.objects.get(pk=res.data["id"])
    assert g.status == "approved" and g.managed_by_platform and g.user.email == "gid@meyzi.uz"
    assert g.languages == ["uz", "en"] and list(g.destinations.all()) == [samarqand]


def test_users_view_block_no_edit(staff_api, admin_user, user):
    U = "/api/v1/control/users/"
    d = staff_api.get(U + f"{user.pk}/").data
    assert d["email"] == user.email and "completed_trips" in d and d["coins"] is None
    # ma'lumotlarni o'zgartirish va o'chirish yo'q
    assert staff_api.patch(M + f"user/{user.pk}/", {"first_name": "X"}, format="json").status_code == 403
    assert staff_api.delete(M + f"user/{user.pk}/").status_code == 403
    assert staff_api.post(M + "user/", {"first_name": "X"}, format="json").status_code == 403
    # bloklash / blokdan chiqarish
    assert (
        staff_api.post(U + f"{user.pk}/block/", {"reason": "Spam"}, format="json").data["is_active"] is False
    )
    user.refresh_from_db()
    assert user.is_active is False
    assert staff_api.post(U + f"{user.pk}/unblock/").data["is_active"] is True
    assert staff_api.post(U + f"{admin_user.pk}/block/").status_code == 400  # o'zini emas
    # ishchi qilish
    res = staff_api.post(U + f"{user.pk}/staff/", {"is_staff": True, "staff_area": "hotels"}, format="json")
    assert res.data == {"is_staff": True, "staff_area": "hotels"}


def test_admin_adds_photos_to_partner_guide_agency_hotel(staff_api, hotel, agency, samarqand):  # noqa: F811
    gu = User.objects.create_user(email="gid-hamkor@example.com", password="x")
    g = GuideProfile.objects.create(
        user=gu,
        slug="hamkor-gid",
        display_name="Hamkor gid",
        phone="+998901112299",
        languages=["uz"],
        price_half_day_uzs=1,
        price_full_day_uzs=1,
        price_per_day_uzs=1,
    )
    # Gid: ro'yxatda "Rasm" havolasi, faqat surat maydoni o'zgaradi
    row = next(r for r in staff_api.get(M + "guide/").data["results"] if r["id"] == g.pk)
    assert row["editable"] is False and row["media_url"] == f"/control/manage/guide/{g.pk}"
    d = staff_api.get(M + f"guide/{g.pk}/").data
    assert d["media_fields"] == ["photo"]
    res = staff_api.patch(
        M + f"guide/{g.pk}/", {"photo": SimpleUploadedFile("g.png", PNG)}, format="multipart"
    )
    assert res.status_code == 200, res.data
    g.refresh_from_db()
    assert g.photo.name.startswith("guides/")
    # boshqa maydon bilan birga — rad etiladi
    res = staff_api.patch(
        M + f"guide/{g.pk}/",
        {"photo": SimpleUploadedFile("g.png", PNG), "display_name": "X"},
        format="multipart",
    )
    assert res.status_code == 403
    g.refresh_from_db()
    assert g.display_name == "Hamkor gid"

    # Agentlik logotipi
    res = staff_api.patch(
        M + f"agency/{agency.pk}/", {"logo": SimpleUploadedFile("l.png", PNG)}, format="multipart"
    )
    assert res.status_code == 200, res.data
    agency.refresh_from_db()
    assert agency.logo.name.startswith("agencies/")

    # Mehmonxona: galereya sahifasiga havola, hamkor mehmonxonasiga rasm qo'shiladi
    row = next(r for r in staff_api.get(M + "hotel/").data["results"] if r["id"] == hotel.pk)
    assert row["media_url"] == f"/control/manage/hotel/{hotel.pk}"
    assert staff_api.get(M + f"hotel/{hotel.pk}/").data["gallery"]["res"] == "hotel_media"
    res = staff_api.post(
        M + "hotel_media/",
        {"hotel": hotel.pk, "image": SimpleUploadedFile("h.png", PNG), "is_cover": "true"},
        format="multipart",
    )
    assert res.status_code == 201, res.data
    assert HotelImage.objects.filter(hotel=hotel, is_cover=True).count() == 1


def test_tour_edit_page_has_gallery_for_partner_tour(staff_api, tour):
    from apps.tours.models import TourMedia

    row = next(r for r in staff_api.get(M + "tour/").data["results"] if r["id"] == tour.pk)
    assert row["editable"] is False and row["media_url"] == f"/control/manage/tour/{tour.pk}"
    res = staff_api.post(
        M + "tour_media/",
        {"tour": tour.pk, "file": SimpleUploadedFile("t.png", PNG), "is_cover": "true"},
        format="multipart",
    )
    assert res.status_code == 201, res.data
    second = staff_api.post(
        M + "tour_media/", {"tour": tour.pk, "file": SimpleUploadedFile("t2.png", PNG)}, format="multipart"
    ).data["id"]
    g = staff_api.get(M + f"tour/{tour.pk}/").data["gallery"]
    assert g["res"] == "tour_media" and g["parent"] == "tour" and g["file_field"] == "file"
    assert [m["is_cover"] for m in g["items"]] == [True, False] and g["items"][0]["url"]
    # muqovani almashtirish va o'chirish
    assert (
        staff_api.patch(M + f"tour_media/{second}/", {"is_cover": "true"}, format="multipart").status_code
        == 200
    )
    assert TourMedia.objects.get(pk=second).is_cover
    assert TourMedia.objects.filter(tour=tour, is_cover=True).count() == 1
    assert staff_api.delete(M + f"tour_media/{second}/").status_code == 204
    # hamkor turi matni — baribir o'zgarmaydi
    assert staff_api.patch(M + f"tour/{tour.pk}/", {"title": "X"}, format="json").status_code == 403
