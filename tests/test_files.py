import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.guides.models import GuideProfile

from .conftest import phone_token
from .media_samples import MP4, PDF, PNG

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"
    return tmp_path


def apply_as_guide(client, samarqand, **files):
    data = {
        "display_name": "Ali Gid",
        "phone": "+998901234567",
        "phone_token": phone_token("+998901234567"),
        "languages": ["uz"],
        "destinations": ["samarqand"],
        "price_half_day_uzs": 1,
        "price_full_day_uzs": 1,
        "price_per_day_uzs": 1,
        "photo": SimpleUploadedFile("men.png", PNG, content_type="image/png"),
        "certificate_file": SimpleUploadedFile("sertifikat.pdf", PDF, content_type="application/pdf"),
        **files,
    }
    return client.post("/api/v1/guides/me/", data, format="multipart")


def test_certificate_is_private(auth_api, admin_api, samarqand, dirs):
    cert = SimpleUploadedFile("sertifikat.pdf", b"%PDF-1.4 test", content_type="application/pdf")
    res = apply_as_guide(auth_api, samarqand, certificate_file=cert)
    assert res.status_code == 201, res.data
    assert "certificate_file" not in res.data  # hech kimga qaytarilmaydi
    assert res.data["has_certificate_file"] is True

    profile = GuideProfile.objects.get()
    assert (dirs / "private" / profile.certificate_file.name).is_file()
    assert not (dirs / "media" / profile.certificate_file.name).exists()

    url = profile.certificate_file.url
    assert url.startswith("/admin/private/")
    assert APIClient().get(url).status_code == 302  # login sahifasiga
    assert auth_api.get(url).status_code == 302  # oddiy foydalanuvchi ham
    admin_api.force_login(admin_api.handler._force_user)
    res = admin_api.get(url)
    assert res.status_code == 200
    assert b"".join(res.streaming_content) == b"%PDF-1.4 test"


def test_private_path_traversal_blocked(admin_api, dirs):
    (dirs / "secret.txt").write_text("x")
    admin_api.force_login(admin_api.handler._force_user)
    assert admin_api.get("/admin/private/../secret.txt").status_code == 404


def test_certificate_wrong_type(auth_api, samarqand):
    bad = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
    res = apply_as_guide(auth_api, samarqand, certificate_file=bad)
    assert res.status_code == 400
    assert "certificate_file" in res.data


def test_tour_media_rules(agency_api, tour, settings):
    url = f"/api/v1/cabinet/tours/{tour.slug}/media/"
    big = SimpleUploadedFile("big.png", PNG + b"0" * (7 * 1024 * 1024), content_type="image/png")
    res = agency_api.post(url, {"file": big}, format="multipart")
    assert res.status_code == 400  # 6 MB dan katta rasm

    def vid(name="v.mp4", data=MP4):
        return SimpleUploadedFile(name, data, content_type="video/mp4")

    # turi fayldan aniqlanadi: "kind=image" deb yuborilgan mp4 — video bo'lib saqlanadi
    res = agency_api.post(url, {"file": vid(), "kind": "image"}, format="multipart")
    assert res.status_code == 201 and res.data["kind"] == "video", res.data
    assert (
        agency_api.post(
            url, {"file": vid(), "kind": "video", "is_cover": True}, format="multipart"
        ).status_code
        == 400
    )
    ok = SimpleUploadedFile("a.png", PNG, content_type="image/png")
    assert agency_api.post(url, {"file": ok, "is_cover": True}, format="multipart").status_code == 201
