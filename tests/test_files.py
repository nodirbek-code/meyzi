import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.guides.models import GuideProfile

pytestmark = pytest.mark.django_db

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture(autouse=True)
def dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"
    return tmp_path


def apply_as_guide(client, samarqand, **files):
    data = {
        "display_name": "Ali Gid",
        "phone": "+998901234567",
        "languages": ["uz"],
        "destinations": ["samarqand"],
        "price_half_day_uzs": 1,
        "price_full_day_uzs": 1,
        "price_per_day_uzs": 1,
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
    big = SimpleUploadedFile("big.png", PNG + b"0" * (11 * 1024 * 1024), content_type="image/png")
    res = agency_api.post(url, {"file": big}, format="multipart")
    assert res.status_code == 400  # 10 MB dan katta rasm

    def vid():
        return SimpleUploadedFile("v.mp4", b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4")

    assert agency_api.post(url, {"file": vid(), "kind": "image"}, format="multipart").status_code == 400
    assert (
        agency_api.post(
            url, {"file": vid(), "kind": "video", "is_cover": True}, format="multipart"
        ).status_code
        == 400
    )
    res = agency_api.post(url, {"file": vid(), "kind": "video"}, format="multipart")
    assert res.status_code == 201, res.data
    ok = SimpleUploadedFile("a.png", PNG, content_type="image/png")
    assert agency_api.post(url, {"file": ok, "is_cover": True}, format="multipart").status_code == 201
