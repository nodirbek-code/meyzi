"""/control → Boshqarish: Excel orqali ommaviy qo'shish (yo'nalish, agentlik, mehmonxona, gid, tur)."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook, load_workbook
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.agencies.models import Agency, AgencyMember
from apps.catalog.models import Destination
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel
from apps.tours.models import Tour, TourCategory

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db
M = "/api/v1/control/manage/"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def xlsx(header: list, rows: list[list], name: str = "data.xlsx") -> SimpleUploadedFile:
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=XLSX)


def upload(client, res, file):
    return client.post(M + f"{res}/import/", {"file": file}, format="multipart")


# ---------- Shablon ----------


@pytest.mark.parametrize("res", ["destination", "agency", "hotel", "guide", "tour"])
def test_template_downloads_without_file_columns(staff_api, samarqand, res):
    r = staff_api.get(M + f"{res}/import/template/")
    assert r.status_code == 200
    assert r["Content-Type"] == XLSX
    wb = load_workbook(io.BytesIO(r.content))
    header = [c.value for c in wb["Ma'lumotlar"][1]]
    assert header and "Yo'riqnoma" in wb.sheetnames
    lowered = " ".join(header).lower()
    for file_label in ("logotip", "rasm", "sertifikat fayli"):
        assert file_label not in lowered, (res, header)


def test_list_meta_marks_importable_sections(staff_api):
    assert staff_api.get(M + "agency/").data["can_import"] is True
    assert staff_api.get(M + "faq/").data["can_import"] is False


def test_template_headers_are_accepted_back(staff_api):
    r = staff_api.get(M + "agency/import/template/")
    header = [c.value for c in load_workbook(io.BytesIO(r.content))["Ma'lumotlar"][1]]
    row = [""] * len(header)
    row[header.index("Nomi *")] = "Shablon Tour"
    res = upload(staff_api, "agency", xlsx(header, [row]))
    assert res.status_code == 201, res.data
    assert Agency.objects.filter(name="Shablon Tour").exists()


# ---------- Muvaffaqiyatli import ----------


def test_import_agencies_with_owner(staff_api):
    f = xlsx(
        ["name", "phone", "inn", "commission_percent", "is_verified", "owner_email"],
        [
            ["Silk Road Travel", 998901112233, 123456789, 10, "Ha", "boss@silk.uz"],
            ["Tog' Sayohat", "+998 90 000 00 00", "", "", "Yo'q", ""],
            [None, None, None, None, None, None],  # bo'sh qator — o'tkaziladi
        ],
    )
    r = upload(staff_api, "agency", f)
    assert r.status_code == 201, r.data
    assert r.data["created"] == 2
    silk = Agency.objects.get(name="Silk Road Travel")
    assert silk.managed_by_platform and silk.slug == "silk-road-travel"
    assert silk.phone == "998901112233" and silk.inn == "123456789"
    assert silk.is_verified is True
    member = AgencyMember.objects.get(agency=silk)
    assert member.user.email == "boss@silk.uz" and member.user.role == User.Role.AGENCY
    assert Agency.objects.get(name="Tog' Sayohat").is_verified is False


def test_import_destinations_then_hotels_use_them(staff_api):
    r = upload(
        staff_api,
        "destination",
        xlsx(
            ["Nomi *", "Viloyat", "Kenglik", "Uzunlik", "Tavsiya etiladi", "E'lon qilingan"],
            [
                ["Termiz", "Surxondaryo viloyati", 37.224, 67.278, "Ha", "Ha"],
                ["Namangan", "Namangan viloyati", None, None, "", "Ha"],
            ],
        ),
    )
    assert r.status_code == 201, r.data
    t = Destination.objects.get(slug="termiz")
    assert t.region == "Surxondaryo viloyati" and t.is_featured and t.is_published
    assert not Destination.objects.get(name="Namangan").is_featured
    r = upload(
        staff_api,
        "hotel",
        xlsx(
            ["Nomi *", "Shahar *", "Manzil *", "Telefon *"],
            [["Oxus Termiz", "Termiz", "Alpomish 1", "+998 76 000 00 01"]],
        ),
    )
    assert r.status_code == 201, r.data
    assert Hotel.objects.get(name="Oxus Termiz").destination == t


def test_import_hotels_by_city_name_and_labels(staff_api, samarqand):
    f = xlsx(
        ["name", "kind", "destination", "stars", "address", "phone", "amenities", "check_in_time"],
        [
            [
                "Registon Plaza",
                "Mehmonxona",
                "samarqand",
                4,
                "Registon ko'chasi 1",
                "+998901234567",
                "wifi, Parking",
                "14:00",
            ]
        ],
    )
    r = upload(staff_api, "hotel", f)
    assert r.status_code == 201, r.data
    h = Hotel.objects.get(name="Registon Plaza")
    assert h.destination == samarqand and h.managed_by_platform
    assert h.status == Hotel.Status.APPROVED
    assert set(h.amenities) == {"wifi", "parking"}


def test_import_guides_creates_accounts(staff_api, samarqand):
    f = xlsx(
        [
            "display_name",
            "phone",
            "languages",
            "destinations",
            "price_half_day_uzs",
            "price_full_day_uzs",
            "price_per_day_uzs",
            "owner_email",
        ],
        [
            [
                "Aziz Karimov",
                "+998901112233",
                "O'zbek, ru",
                "Samarqand",
                "300 000",
                500000,
                450000,
                "aziz@gid.uz",
            ]
        ],
    )
    r = upload(staff_api, "guide", f)
    assert r.status_code == 201, r.data
    g = GuideProfile.objects.get(display_name="Aziz Karimov")
    assert g.user.email == "aziz@gid.uz" and g.user.role == User.Role.GUIDE
    assert g.languages == ["uz", "ru"] and g.price_half_day_uzs == 300000
    assert list(g.destinations.all()) == [samarqand]
    assert not g.photo and not g.certificate_file  # fayllar — keyin qo'lda


def test_import_tours_resolves_agency_category_and_lists(staff_api, samarqand):
    Agency.objects.create(name="MEYZI", slug="meyzi", is_platform=True)
    TourCategory.objects.create(name="Tog'", slug="tog")
    f = xlsx(
        [
            "agency",
            "destination",
            "title",
            "categories",
            "duration_days",
            "meeting_point",
            "price_uzs",
            "cancellation_policy",
            "included",
            "departure_time",
            "status",
        ],
        [
            [
                "MEYZI",
                "Samarqand",
                "Zomin 2 kun",
                "Tog'",
                2,
                "Toshkent, Amir Temur xiyoboni",
                "890 000",
                "Bepul bekor qilish",
                "Transport; Tushlik\nGid",
                "06:00",
                "published",
            ]
        ],
    )
    r = upload(staff_api, "tour", f)
    assert r.status_code == 201, r.data
    t = Tour.objects.get(title="Zomin 2 kun")
    assert t.price_uzs == 890000 and t.cancellation_policy == "free"
    assert t.included == ["Transport", "Tushlik", "Gid"]
    assert t.departure_time.strftime("%H:%M") == "06:00"
    assert t.status == Tour.Status.PUBLISHED and t.published_at is not None
    assert [c.slug for c in t.categories.all()] == ["tog"]


# ---------- Xatolar: hech narsa saqlanmaydi ----------


def test_bad_row_rolls_back_whole_file(staff_api):
    f = xlsx(
        ["name", "commission_percent"],
        [["Yaxshi Tour", 10], ["", 5], ["Uchinchi", "ko'p"]],
    )
    r = upload(staff_api, "agency", f)
    assert r.status_code == 400
    assert [row["row"] for row in r.data["rows"]] == [3, 4]
    assert "Raqam" in " ".join(r.data["rows"][1]["errors"])
    assert not Agency.objects.filter(name__in=["Yaxshi Tour", "Uchinchi"]).exists()


def test_guide_rows_rolled_back_do_not_leave_accounts(staff_api, samarqand):
    head = [
        "display_name",
        "phone",
        "languages",
        "destinations",
        "price_half_day_uzs",
        "price_full_day_uzs",
        "price_per_day_uzs",
        "owner_email",
    ]
    f = xlsx(
        head,
        [
            ["A", "1", "uz", "Samarqand", 1, 1, 1, "a@gid.uz"],
            ["B", "2", "uz", "Samarqand", 1, 1, 1, "a@gid.uz"],
        ],
    )
    r = upload(staff_api, "guide", f)
    assert r.status_code == 400
    assert r.data["rows"][0]["row"] == 3  # bitta email — ikkinchi gid bo'lmaydi
    assert not User.objects.filter(email="a@gid.uz").exists()
    assert not GuideProfile.objects.exists()


def test_unknown_reference_and_option_are_reported(staff_api, samarqand):
    f = xlsx(["name", "destination", "address", "phone", "kind"], [["X", "Paris", "a", "1", "Saroy"]])
    r = upload(staff_api, "hotel", f)
    assert r.status_code == 400
    text = " ".join(r.data["rows"][0]["errors"])
    assert "«Paris» topilmadi" in text and "Ruxsat etilgan" in text


def test_tour_for_partner_owned_agency_is_rejected(staff_api, agency, samarqand):
    """Hamkor o'zi yaratgan agentlik nomiga tur qo'shib bo'lmaydi (forma bilan bir xil qoida)."""
    TourCategory.objects.create(name="Tog'", slug="tog")
    f = xlsx(
        ["agency", "destination", "title", "categories", "meeting_point", "price_uzs"],
        [[agency.name, "Samarqand", "T", "Tog'", "m", 1]],
    )
    r = upload(staff_api, "tour", f)
    assert r.status_code == 400 and "topilmadi" in " ".join(r.data["rows"][0]["errors"])


@pytest.mark.parametrize(
    ("file", "message"),
    [
        (SimpleUploadedFile("a.csv", b"name\nX"), ".xlsx"),
        (SimpleUploadedFile("a.xlsx", b"not a zip"), "o'qib bo'lmadi"),
    ],
)
def test_bad_files(staff_api, file, message):
    r = upload(staff_api, "agency", file)
    assert r.status_code == 400 and message in r.data["file"]


def test_unknown_and_missing_columns(staff_api):
    r = upload(staff_api, "agency", xlsx(["name", "Logo URL"], [["X", "y"]]))
    assert r.status_code == 400 and "Logo URL" in r.data["file"]
    r = upload(staff_api, "agency", xlsx(["phone"], [["1"]]))
    assert r.status_code == 400 and "Majburiy" in r.data["file"]
    r = upload(staff_api, "agency", xlsx(["name"], []))
    assert r.status_code == 400 and "ma'lumot yo'q" in r.data["file"]


# ---------- Ruxsatlar ----------


def test_only_main_admin(api, auth_api, db):
    mod = User.objects.create_user(email="m@meyzi.uz", password=PASSWORD, is_staff=True, staff_area="hotels")
    mod_api = APIClient()
    mod_api.force_authenticate(mod)
    for client in (api, auth_api, mod_api):
        assert client.get(M + "agency/import/template/").status_code in (401, 403)
        assert upload(client, "agency", xlsx(["name"], [["X"]])).status_code in (401, 403)
    assert not Agency.objects.filter(name="X").exists()


def test_not_importable_section(staff_api):
    assert staff_api.get(M + "faq/import/template/").status_code == 404
    assert upload(staff_api, "faq", xlsx(["question"], [["?"]])).status_code == 404
