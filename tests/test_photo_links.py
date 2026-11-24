"""/control → Excel orqali rasm havolalari (gid, agentlik, mehmonxona)."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook, load_workbook
from rest_framework.test import APIClient

from apps.core import control_photo_links as pl
from apps.core.media_import import Skip
from apps.hotels.models import HotelImage

from .media_samples import MP4, PNG
from .test_hotels import hotel, owner  # noqa: F401 — fixture'lar

pytestmark = pytest.mark.django_db
M = "/api/v1/control/manage/"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture(autouse=True)
def dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


@pytest.fixture
def fake_net(monkeypatch):
    """Internetsiz: havola oxiri bo'yicha javob."""

    def download(url, kind):
        if url.endswith("/page"):
            raise Skip("Havola rasm emas.")
        return ("mp4", MP4) if kind == "video" else ("png", PNG)

    monkeypatch.setattr(pl, "download", download)


def _xlsx(header, rows):
    wb = Workbook()
    wb.active.append(header)
    for r in rows:
        wb.active.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile("h.xlsx", buf.getvalue(), content_type=XLSX)


def test_template_lists_existing_records(staff_api, agency):
    res = staff_api.get(M + "agency/photo-links/template/")
    assert res.status_code == 200
    ws = load_workbook(io.BytesIO(res.content)).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0][:3] == ("Nomi *", "Slug", "Logotip havolasi")
    assert ("Vodiy Tour", "vodiy-tour") in [r[:2] for r in rows[1:]]
    assert staff_api.get(M + "tour/photo-links/template/").status_code == 404


def test_agency_logo_and_hotel_gallery_from_links(staff_api, agency, hotel, fake_net):  # noqa: F811
    up = _xlsx(["Nomi *", "Slug", "Logotip havolasi"], [["Vodiy Tour", "vodiy-tour", "https://x.uz/l.png"]])
    res = staff_api.post(M + "agency/photo-links/", {"file": up}, format="multipart")
    assert res.status_code == 200 and res.data["done"] == 1, res.data
    agency.refresh_from_db()
    assert agency.logo.name.startswith("agencies/vodiy-tour")

    header = ["Nomi *", "Slug", "Rasm 1", "Rasm 2", "Video 1"]
    up = _xlsx(
        header,
        [
            [hotel.name, hotel.slug, "https://x.uz/a.png", "https://x.uz/page", "https://x.uz/v.mp4"],
            ["Yo'q mehmonxona", "", "https://x.uz/b.png", None, None],
        ],
    )
    res = staff_api.post(M + "hotel/photo-links/", {"file": up}, format="multipart")
    assert res.status_code == 200, res.data
    assert res.data["done"] == 2 and res.data["failed"] == 2
    msgs = {(r["column"], r["ok"]) for r in res.data["results"]}
    assert ("Rasm 1", True) in msgs and ("Rasm 2", False) in msgs and ("Video 1", True) in msgs
    imgs = HotelImage.objects.filter(hotel=hotel)
    assert imgs.filter(kind="image", is_cover=True).count() == 1
    assert imgs.filter(kind="video").count() == 1


def test_bad_file_and_regular_user(staff_api, auth_api):
    up = _xlsx(["Boshqa"], [["x"]])
    assert staff_api.post(M + "guide/photo-links/", {"file": up}, format="multipart").status_code == 400
    assert auth_api.get(M + "guide/photo-links/template/").status_code == 403


def test_download_rejects_private_hosts_and_non_images():
    with pytest.raises(Skip):
        pl.download("http://127.0.0.1/x.png", "image")
    with pytest.raises(Skip):
        pl.download("ftp://example.com/x.png", "image")
    with pytest.raises(Skip):
        pl.download("http://localhost/x.png", "image")


def test_download_sniffs_real_content(monkeypatch):
    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(pl, "_check_host", lambda url: None)
    monkeypatch.setattr(pl._opener, "open", lambda req, timeout: Resp(PNG))
    assert pl.download("https://x.uz/no-extension", "image") == ("png", PNG)
    monkeypatch.setattr(pl._opener, "open", lambda req, timeout: Resp(b"<html>Instagram</html>"))
    with pytest.raises(Skip, match="rasm emas"):
        pl.download("https://instagram.com/p/x", "image")
    monkeypatch.setattr(pl._opener, "open", lambda req, timeout: Resp(MP4))
    assert pl.download("https://x.uz/v", "video")[0] == "mp4"
