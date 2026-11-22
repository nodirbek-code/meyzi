"""Yuklash qoidalari: haqiqiy format, hajm (rasm 6 MB, video 20 MB), galereya: 20 rasm, 4 video."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.files import document_rule, image_rule, video_rule
from apps.hotels.models import HotelImage
from apps.tours.models import TourMedia

from .media_samples import JPEG, MP4, PDF, PNG
from .test_hotels import hotel, owner, owner_api  # noqa: F401 — fixture'lar

pytestmark = pytest.mark.django_db

MB = 1024 * 1024


@pytest.fixture(autouse=True)
def media_dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"


def up(name, data, ctype="application/octet-stream"):
    return SimpleUploadedFile(name, data, content_type=ctype)


# ---------- Qoida darajasida ----------


@pytest.mark.parametrize(
    ("rule", "name", "data"),
    [
        (image_rule, "a.png", PNG),
        (image_rule, "a.jpg", JPEG),
        (image_rule, "a.jpeg", JPEG),
        (video_rule, "v.mp4", MP4),
        (video_rule, "v.webm", bytes.fromhex("1a45dfa3") + b"\x00" * 12),
        (document_rule, "s.pdf", PDF),
        (document_rule, "s.png", PNG),
    ],
)
def test_valid_files_pass(rule, name, data):
    rule(up(name, data))


@pytest.mark.parametrize(
    ("rule", "name", "data"),
    [
        (image_rule, "virus.png", b"MZ\x90\x00 bu exe"),  # kengaytma rasm, ichi emas
        (image_rule, "a.jpg", PNG),  # PNG ichida, .jpg deb nomlangan
        (image_rule, "a.gif", b"GIF89a"),  # ruxsat etilmagan format
        (image_rule, "buzuq.png", PNG[:20]),  # buzilgan rasm
        (video_rule, "v.mp4", b"bu video emas" * 3),
        (video_rule, "v.webm", MP4),
        (video_rule, "v.avi", b"RIFF...."),
        (document_rule, "s.pdf", b"<html>pdf emas</html>"),
        (document_rule, "s.docx", b"PK\x03\x04"),
    ],
)
def test_fake_or_wrong_format_rejected(rule, name, data):
    with pytest.raises(ValidationError):
        rule(up(name, data))


def test_size_limits():
    image_rule(up("ok.png", PNG + b"0" * (5 * MB)))
    with pytest.raises(ValidationError, match="6 MB"):
        image_rule(up("big.png", PNG + b"0" * (6 * MB + 1)))
    video_rule(up("ok.mp4", MP4 + b"0" * (19 * MB)))
    with pytest.raises(ValidationError, match="20 MB"):
        video_rule(up("big.mp4", MP4 + b"0" * (20 * MB + 1)))
    with pytest.raises(ValidationError, match="6 MB"):
        document_rule(up("big.pdf", PDF + b"0" * (6 * MB + 1)))


# ---------- Turlar: 20 rasm, 4 video ----------


def test_tour_gallery_limits(agency_api, tour):
    url = f"/api/v1/cabinet/tours/{tour.slug}/media/"
    TourMedia.objects.bulk_create([TourMedia(tour=tour, kind="image", file="tours/x.png") for _ in range(20)])
    res = agency_api.post(url, {"file": up("21.png", PNG, "image/png")}, format="multipart")
    assert res.status_code == 400 and "20" in str(res.data)

    for i in range(4):
        res = agency_api.post(url, {"file": up(f"{i}.mp4", MP4, "video/mp4")}, format="multipart")
        assert res.status_code == 201, res.data
    res = agency_api.post(url, {"file": up("5.mp4", MP4, "video/mp4")}, format="multipart")
    assert res.status_code == 400 and "4" in str(res.data)


def test_tour_fake_image_rejected(agency_api, tour):
    url = f"/api/v1/cabinet/tours/{tour.slug}/media/"
    res = agency_api.post(url, {"file": up("rasm.jpg", b"not an image", "image/jpeg")}, format="multipart")
    assert res.status_code == 400 and "file" in res.data


# ---------- Mehmonxonalar: rasm va video ----------

HOTEL_MEDIA = "/api/v1/cabinet/hotel/images/"


def test_hotel_can_upload_images_and_videos(owner_api, hotel):  # noqa: F811
    res = owner_api.post(
        HOTEL_MEDIA, {"image": up("lobby.jpg", JPEG, "image/jpeg"), "is_cover": True}, format="multipart"
    )
    assert res.status_code == 201 and res.data["kind"] == "image", res.data
    res = owner_api.post(HOTEL_MEDIA, {"image": up("tour.mp4", MP4, "video/mp4")}, format="multipart")
    assert res.status_code == 201 and res.data["kind"] == "video", res.data
    res = owner_api.post(
        HOTEL_MEDIA, {"image": up("v.mp4", MP4, "video/mp4"), "is_cover": True}, format="multipart"
    )
    assert res.status_code == 400  # video muqova bo'lmaydi
    res = owner_api.post(
        HOTEL_MEDIA, {"image": up("big.mp4", MP4 + b"0" * (20 * MB + 1), "video/mp4")}, format="multipart"
    )
    assert res.status_code == 400


def test_hotel_gallery_limits(owner_api, hotel):  # noqa: F811
    HotelImage.objects.bulk_create(
        [HotelImage(hotel=hotel, kind="image", image="hotels/x.png") for _ in range(20)]
    )
    HotelImage.objects.bulk_create(
        [HotelImage(hotel=hotel, kind="video", image="hotels/x.mp4") for _ in range(4)]
    )
    res = owner_api.post(HOTEL_MEDIA, {"image": up("a.png", PNG, "image/png")}, format="multipart")
    assert res.status_code == 400 and "20" in str(res.data)
    res = owner_api.post(HOTEL_MEDIA, {"image": up("a.mp4", MP4, "video/mp4")}, format="multipart")
    assert res.status_code == 400 and "4" in str(res.data)
