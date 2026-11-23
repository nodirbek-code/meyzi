"""Hamkorlik arizalarini Excel'dan qo'shish: yozuvlar hamkor yuborgandek tekshiruv navbatiga tushadi."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.agencies.models import Agency, AgencyApplication
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel, HotelMember
from apps.notifications.models import TelegramMessage

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db
M = "/api/v1/control/manage/"
C = "/api/v1/control/"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def upload(client, res, header, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    f = SimpleUploadedFile("a.xlsx", buf.getvalue(), content_type=XLSX)
    return client.post(M + f"{res}/import/", {"file": f}, format="multipart")


def test_agency_applications_land_as_new(staff_api):
    r = upload(
        staff_api,
        "agency_application",
        ["Agentlik nomi", "Mas'ul shaxs", "Telefon", "Email", "Izoh"],
        [["Oqtosh Travel", "Ali Valiyev", "+998 90 111 22 33", "ali@oqtosh.uz", "Tog' turlari"]],
    )
    assert r.status_code == 201, r.data
    app = AgencyApplication.objects.get(agency_name="Oqtosh Travel")
    assert app.status == AgencyApplication.Status.NEW and app.agency is None
    assert not Agency.objects.filter(name="Oqtosh Travel").exists()  # agentlik faqat tasdiqdan keyin
    assert not TelegramMessage.objects.exists()  # import adminlarga 15 ta xabar yubormaydi
    rows = staff_api.get(C + "items/application/", {"state": "pending"}).data["results"]
    assert [x["title"] for x in rows] == ["Oqtosh Travel"]


HEAD_GUIDE = [
    "Ism (ko'rinadigan)",
    "Telefon",
    "Shaharlar",
    "Yarim kun (4 soat), so'm",
    "To'liq kun (8 soat), so'm",
    "Ko'p kunlik, 1 kun uchun, so'm",
    "Tillar",
    "Gid akkauntining emaili",
]


def test_guide_applications_go_to_moderator_precheck(staff_api, samarqand):
    r = upload(
        staff_api,
        "guide_application",
        HEAD_GUIDE,
        [
            [
                "Laylo Karimova",
                "+998901234567",
                "Samarqand",
                300000,
                500000,
                450000,
                "O'zbek, Ingliz",
                "laylo@g.uz",
            ]
        ],
    )
    assert r.status_code == 201, r.data
    g = GuideProfile.objects.get(display_name="Laylo Karimova")
    assert g.status == GuideProfile.Status.PENDING and g.prechecked_at is None and not g.managed_by_platform
    assert g.user.email == "laylo@g.uz" and g.user.role == User.Role.GUIDE
    assert g.languages == ["uz", "en"] and not g.is_certified
    rows = staff_api.get(C + "items/guide/", {"state": "precheck"}).data["results"]
    assert [x["title"] for x in rows] == ["Laylo Karimova"]


def test_hotel_applications_get_owner_and_pending(staff_api, samarqand):
    head = ["Nomi", "Shahar", "Manzil", "Telefon", "Yulduz", "Egasining emaili"]
    r = upload(
        staff_api,
        "hotel_application",
        head,
        [["Bog'i Eram", "Samarqand", "Toshkent ko'chasi 5", "+998662000000", 4, "eram@h.uz"]],
    )
    assert r.status_code == 201, r.data
    h = Hotel.objects.get(name="Bog'i Eram")
    assert h.status == Hotel.Status.PENDING and not h.managed_by_platform
    m = HotelMember.objects.get(hotel=h)
    assert (
        m.user.email == "eram@h.uz" and m.role == HotelMember.Role.OWNER and m.user.role == User.Role.BUSINESS
    )


def test_duplicate_owner_rolls_back_whole_file(staff_api, samarqand):
    rows = [
        ["A", "+998901", "Samarqand", 1, 1, 1, "O'zbek", "same@g.uz"],
        ["B", "+998902", "Samarqand", 1, 1, 1, "O'zbek", "same@g.uz"],
    ]
    r = upload(staff_api, "guide_application", HEAD_GUIDE, rows)
    assert r.status_code == 400
    assert r.data["rows"][0]["row"] == 3 and "allaqachon" in " ".join(r.data["rows"][0]["errors"])
    assert not GuideProfile.objects.exists() and not User.objects.filter(email="same@g.uz").exists()


def test_admin_only_columns_are_not_in_template(staff_api):
    from openpyxl import load_workbook

    r = staff_api.get(M + "guide_application/import/template/")
    header = [c.value for c in load_workbook(io.BytesIO(r.content))["Ma'lumotlar"][1]]
    assert "Sertifikat tasdiqlangan" not in " ".join(header)
    assert not any("komissiya" in h.lower() for h in header)


def test_import_button_only_for_main_admin(staff_api, api):
    assert staff_api.get(C + "items/application/").data["import_key"] == "agency_application"
    assert staff_api.get(C + "items/tour/").data["import_key"] is None
    User.objects.create_user(email="mod@meyzi.uz", password=PASSWORD, is_staff=True, staff_area="guides")
    mod = APIClient()
    mod.force_authenticate(User.objects.get(email="mod@meyzi.uz"))
    assert mod.get(C + "items/guide/").data["import_key"] is None
    assert mod.get(M + "guide_application/import/template/").status_code == 403


def test_application_sections_are_not_crud(staff_api):
    assert staff_api.get(M + "agency_application/").status_code == 404
