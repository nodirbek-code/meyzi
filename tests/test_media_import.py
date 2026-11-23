"""ZIP orqali ommaviy media: papka nomi bo'yicha biriktirish, takrorsiz, qismlab ishlash."""

import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.agencies.models import Agency
from apps.catalog.models import Place
from apps.core.media_import import parse_path
from apps.core.models import MediaImportJob
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel, HotelImage
from apps.tours.models import TourMedia

from .media_samples import JPEG, MP4, PNG, image_bytes

pytestmark = pytest.mark.django_db
U = "/api/v1/control/media-import/"


@pytest.fixture(autouse=True)
def dirs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"


@pytest.fixture
def staff_api(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def make_zip(files: dict) -> SimpleUploadedFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return SimpleUploadedFile("media.zip", buf.getvalue(), content_type="application/zip")


def run(client, files):
    r = client.post(U, {"file": make_zip(files)}, format="multipart")
    assert r.status_code == 201, r.data
    while r.data["status"] in ("queued", "running"):
        r = client.get(U + f"{r.data['id']}/")
    return r.data


@pytest.fixture
def objects(tour, samarqand, registon):
    hotel = Hotel.objects.create(
        name="Registon Plaza",
        slug="registon-plaza",
        destination=samarqand,
        address="x",
        phone="+998",
        stars=4,
    )
    u = User.objects.create_user(email="g@g.uz", password="x")
    guide = GuideProfile.objects.create(
        user=u,
        slug="jasur-toshmatov",
        display_name="Jasur Toshmatov",
        phone="+998",
        languages=["uz"],
        price_half_day_uzs=1,
        price_full_day_uzs=1,
        price_per_day_uzs=1,
    )
    return {
        "tour": tour,
        "hotel": hotel,
        "guide": guide,
        "agency": tour.agency,
        "place": registon,
        "dest": samarqand,
    }


def test_parse_path_variants():
    assert parse_path("turlar/samarqand-1-kun/1.jpg") == ("tour", "samarqand-1-kun", "1.jpg")
    assert parse_path("MEYZI rasmlar/Gidlar/Jasur Toshmatov.jpg") == (
        "guide",
        "Jasur Toshmatov",
        "Jasur Toshmatov.jpg",
    )
    assert parse_path("hotels/registon-plaza/zal/2.png")[0:2] == ("hotel", "registon-plaza")


def test_zip_attaches_everything_by_folder(staff_api, objects):
    data = run(
        staff_api,
        {
            "turlar/samarqand-1-kun/1.jpg": JPEG,
            "turlar/samarqand-1-kun/2.png": PNG,
            "turlar/samarqand-1-kun/video.mp4": MP4,
            "mehmonxonalar/Registon Plaza/a.jpg": JPEG,  # nomi bilan ham topiladi
            "gidlar/jasur-toshmatov.jpg": JPEG,
            f"agentliklar/{objects['agency'].slug}.png": PNG,
            "yonalishlar/samarqand.jpg": JPEG,
            f"joylar/{objects['place'].slug}/muqova.jpg": JPEG,
            f"joylar/{objects['place'].slug}/ichki.jpg": image_bytes("JPEG", (3, 3)),
            f"joylar/{objects['place'].slug}/audio.mp3": b"ID3audio",
            "__MACOSX/turlar/._1.jpg": b"x",  # tashlab yuboriladi
        },
    )
    assert data["status"] == "done" and data["total"] == 10 and data["attached"] == 10, data["report"]
    t = objects["tour"]
    media = list(TourMedia.objects.filter(tour=t).order_by("sort_order"))
    assert [m.kind for m in media] == ["image", "image", "video"] and [m.is_cover for m in media] == [
        True,
        False,
        False,
    ]
    assert HotelImage.objects.get(hotel=objects["hotel"]).is_cover
    objects["guide"].refresh_from_db()
    assert objects["guide"].photo
    assert Agency.objects.get(pk=objects["agency"].pk).logo
    objects["dest"].refresh_from_db()
    assert objects["dest"].cover_image
    p = Place.objects.get(pk=objects["place"].pk)
    assert p.cover_image and p.audio_guide and p.images.count() == 1
    assert not MediaImportJob.objects.get(pk=data["id"]).file  # ZIP o'chirildi


def test_reupload_does_not_duplicate_and_reports_problems(staff_api, objects):
    files = {"turlar/samarqand-1-kun/1.jpg": JPEG}
    run(staff_api, files)
    data = run(
        staff_api,
        {
            **files,
            "turlar/yoq-tur/1.jpg": JPEG,
            "turlar/samarqand-1-kun/soxta.jpg": b"bu rasm emas",
            "turlar/samarqand-1-kun/hujjat.pdf": b"%PDF-1.4",
            "rasmlar/1.jpg": JPEG,
        },
    )
    assert data["attached"] == 0 and data["failed"] == 5
    msgs = {r["path"]: r["message"] for r in data["report"]}
    assert "allaqachon" in msgs["turlar/samarqand-1-kun/1.jpg"]
    assert "topilmadi" in msgs["turlar/yoq-tur/1.jpg"]
    assert "rasm emas" in msgs["turlar/samarqand-1-kun/soxta.jpg"]
    assert "Bo'lim" in msgs["rasmlar/1.jpg"]
    assert TourMedia.objects.filter(tour=objects["tour"]).count() == 1


def test_processed_in_batches_by_scheduler(staff_api, objects):
    files = {f"turlar/samarqand-1-kun/{i}.jpg": image_bytes("JPEG", (i + 2, 2)) for i in range(12)}
    r = staff_api.post(U, {"file": make_zip(files)}, format="multipart")
    assert r.data["status"] == "running" and r.data["processed"] == 5  # birinchi qism darhol
    call_command("process_media_imports")
    job = MediaImportJob.objects.get(pk=r.data["id"])
    assert job.status == "done" and job.attached == 12


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [("a.rar", b"x", ".zip"), ("a.zip", b"not a zip", "o'qib bo'lmadi")],
)
def test_bad_upload(staff_api, name, content, message):
    r = staff_api.post(U, {"file": SimpleUploadedFile(name, content)}, format="multipart")
    assert r.status_code == 400 and message in str(r.data["file"])


def test_only_main_admin(api, db):
    mod = User.objects.create_user(email="m@m.uz", password="x", is_staff=True, staff_area="hotels")
    c = APIClient()
    c.force_authenticate(mod)
    assert c.get(U).status_code == 403
    assert api.get(U).status_code in (401, 403)
