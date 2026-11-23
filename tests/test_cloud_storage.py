"""Cloudinary storage (Render: disk vaqtinchalik) — Cloudinary'ga haqiqiy so'rov yuborilmaydi (mock)."""

from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.catalog.models import Destination
from apps.core.cloud_storage import CloudinaryStorage
from apps.core.files import PrivateStorage, private_storage

from .media_samples import PDF, PNG

CLOUD_URL = "cloudinary://key123:sec%2Fret@demo-cloud"


@pytest.fixture
def cloud(settings):
    settings.CLOUDINARY_URL = CLOUD_URL
    settings.CLOUDINARY_FOLDER = "meyzi"
    with (
        mock.patch("cloudinary.uploader.upload") as upload,
        mock.patch("cloudinary.uploader.destroy") as destroy,
    ):
        yield {"upload": upload, "destroy": destroy}


def test_configures_sdk_from_settings(cloud):
    import cloudinary

    CloudinaryStorage()
    cfg = cloudinary.config()
    assert (cfg.cloud_name, cfg.api_key, cfg.api_secret) == ("demo-cloud", "key123", "sec/ret")


def test_bad_url_is_rejected(settings):
    from django.core.exceptions import ImproperlyConfigured

    settings.CLOUDINARY_URL = "https://wrong"
    with pytest.raises(ImproperlyConfigured):
        CloudinaryStorage()


@pytest.mark.parametrize(
    ("name", "rtype", "public_id"),
    [
        ("destinations/x.jpg", "image", "meyzi/destinations/x"),
        ("hotels/v.mp4", "video", "meyzi/hotels/v"),
        ("places/audio/a.mp3", "video", "meyzi/places/audio/a"),
        ("docs/f.pdf", "raw", "meyzi/docs/f.pdf"),
    ],
)
def test_resource_type_and_public_id(cloud, name, rtype, public_id):
    s = CloudinaryStorage()
    assert s._resource_type(name) == rtype
    assert s._public_id(name) == public_id


def test_save_uploads_with_unique_name_and_builds_url(cloud):
    s = CloudinaryStorage()
    name = s.save("destinations/samarqand.jpg", SimpleUploadedFile("samarqand.jpg", PNG))
    assert name.startswith("destinations/samarqand_") and name.endswith(".jpg")
    kwargs = cloud["upload"].call_args.kwargs
    assert kwargs["public_id"] == "meyzi/" + name[: -len(".jpg")]
    assert (kwargs["resource_type"], kwargs["type"], kwargs["overwrite"]) == ("image", "upload", False)
    url = s.url(name)
    assert url.startswith("https://res.cloudinary.com/demo-cloud/image/upload/")
    assert url.endswith(name[: -len(".jpg")] + ".jpg")


def test_delete(cloud):
    CloudinaryStorage().delete("hotels/v_abc.mp4")
    cloud["destroy"].assert_called_once_with(
        "meyzi/hotels/v_abc", invalidate=True, resource_type="video", type="upload"
    )


def test_private_storage_switches_to_authenticated(cloud):
    s = private_storage()
    assert isinstance(s, CloudinaryStorage) and s.private
    s.save("certificates/c.pdf", SimpleUploadedFile("c.pdf", PDF))
    kwargs = cloud["upload"].call_args.kwargs
    assert (kwargs["resource_type"], kwargs["type"]) == ("raw", "authenticated")
    assert kwargs["public_id"].startswith("meyzi/private/certificates/c_")
    assert s.url("certificates/c.pdf") == "/control/admin/private/certificates/c.pdf"  # ochiq havola yo'q
    signed = s._delivery_url("certificates/c.pdf")
    assert "/raw/authenticated/s--" in signed  # imzolangan


def test_private_storage_local_without_cloudinary(settings):
    settings.CLOUDINARY_URL = ""
    assert isinstance(private_storage(), PrivateStorage)


def test_private_file_view_streams_from_cloudinary(cloud, admin_user):
    c = APIClient()
    c.force_login(admin_user)
    with mock.patch.object(CloudinaryStorage, "_open") as op:
        from django.core.files.base import ContentFile

        op.return_value = ContentFile(PDF, name="certificates/c.pdf")
        res = c.get("/control/admin/private/certificates/c.pdf")
    assert res.status_code == 200 and b"".join(res.streaming_content) == PDF
    op.assert_called_once()
    with mock.patch.object(CloudinaryStorage, "_open", side_effect=FileNotFoundError):
        assert c.get("/control/admin/private/certificates/yoq.pdf").status_code == 404


def test_edit_does_not_recheck_saved_file(settings, tmp_path, admin_user):
    """Tahrirlashda eski (o'zgarmagan) rasm qayta o'qilmaydi — fayl yo'qolgan bo'lsa ham saqlanadi."""
    settings.MEDIA_ROOT = tmp_path / "media"
    d = Destination.objects.create(name="Xiva", slug="xiva")
    d.cover_image.save("x.png", SimpleUploadedFile("x.png", PNG))
    (tmp_path / "media" / d.cover_image.name).unlink()  # Render'dagidek: bazada bor, diskda yo'q

    c = APIClient()
    c.force_authenticate(admin_user)
    res = c.patch(f"/api/v1/control/manage/destination/{d.pk}/", {"region": "Xorazm"}, format="json")
    assert res.status_code == 200, res.content
    d.refresh_from_db()
    assert d.region == "Xorazm"


def test_new_upload_still_validated(settings, tmp_path, admin_user):
    settings.MEDIA_ROOT = tmp_path / "media"
    d = Destination.objects.create(name="Nukus", slug="nukus")
    c = APIClient()
    c.force_authenticate(admin_user)
    fake = SimpleUploadedFile("soxta.png", b"bu rasm emas")
    res = c.patch(f"/api/v1/control/manage/destination/{d.pk}/", {"cover_image": fake}, format="multipart")
    assert res.status_code == 400
