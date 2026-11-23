"""ZIP orqali ommaviy rasm/video yuklash — /control → Media (faqat asosiy admin).

ZIP tuzilishi (papka nomi — yozuvning slug'i yoki nomi; ruscha/inglizcha bo'lim nomlari ham bo'ladi):

    turlar/<tur-slug>/1.jpg, 2.jpg, video.mp4      → tur galereyasi (birinchi rasm — muqova, agar yo'q bo'lsa)
    mehmonxonalar/<slug>/...                      → mehmonxona galereyasi
    joylar/<slug>/...                             → joy: 1-rasm muqova, keyingilari galereya; mp3 — audio
    gidlar/<slug>.jpg  yoki  gidlar/<slug>/x.jpg   → gid surati
    agentliklar/<slug>.png                        → agentlik logotipi
    yonalishlar/<slug>.jpg                        → yo'nalish muqovasi

Fayllar odatdagidek tekshiriladi (format, hajm, galereya chegarasi). Bir xil fayl bir yozuvga ikki marta
biriktirilmaydi (`MediaFingerprint`), shuning uchun ZIP'ni qayta yuklash xavfsiz. Ish qismlab bajariladi:
admin sahifasi holatni so'raganda va scheduler (`process_media_imports`) har siklda — Render'da so'rov
vaqti chegarasiga tushmaslik uchun.
"""

import hashlib
import posixpath
import zipfile

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from .files import IMAGE_EXTS, VIDEO_EXTS, _ext, check_gallery_limit, image_rule, media_kind, media_rule
from .models import MediaFingerprint, MediaImportJob

MAX_ZIP_MB = 100  # Next proxy so'rovni xotirada ushlaydi — Render free (512 MB) uchun xavfsiz chegara
MAX_FILES = 1500
BATCH = 15  # bir martada nechta fayl (≈ 15–30 s Cloudinary bilan)
AUDIO_EXTS = ("mp3", "m4a", "ogg")
SKIP_PARTS = ("__macosx",)
SKIP_NAMES = ("thumbs.db", ".ds_store", "desktop.ini")

SECTIONS = {
    "tour": ("turlar", "tours", "туры"),
    "hotel": ("mehmonxonalar", "hotels", "гостиницы", "отели"),
    "place": ("joylar", "places", "diqqatga-sazovor-joylar", "места"),
    "guide": ("gidlar", "guides", "гиды"),
    "agency": ("agentliklar", "agencies", "агентства"),
    "destination": ("yonalishlar", "yo'nalishlar", "destinations", "направления"),
}
SECTION_TITLE = {
    "tour": "Tur",
    "hotel": "Mehmonxona",
    "place": "Joy",
    "guide": "Gid",
    "agency": "Agentlik",
    "destination": "Yo'nalish",
}
_ALIAS = {_a: key for key, aliases in SECTIONS.items() for _a in aliases}


class Skip(Exception):
    pass


def _norm(s: str) -> str:
    return slugify(s.replace("'", "").replace("‘", "").replace("’", "").replace("ʻ", ""))


def media_entries(zf: zipfile.ZipFile) -> list[str]:
    out = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/")
        parts = [p for p in name.split("/") if p]
        if (
            any(p.lower() in SKIP_PARTS or p.startswith(".") for p in parts)
            or parts[-1].lower() in SKIP_NAMES
        ):
            continue
        out.append(name)
    return sorted(out)


def parse_path(path: str) -> tuple[str, str, str]:
    """→ (bo'lim, yozuv kaliti, fayl nomi). Ustki "ildiz" papka bo'lsa o'tkazib yuboriladi."""
    parts = [p for p in path.split("/") if p]
    for i, p in enumerate(parts):
        section = _ALIAS.get(p.lower()) or _ALIAS.get(_norm(p))
        if section is None:
            continue
        rest = parts[i + 1 :]
        if not rest:
            break
        if len(rest) == 1:  # gidlar/jasur-toshmatov.jpg
            return section, posixpath.splitext(rest[0])[0], rest[0]
        return section, rest[0], rest[-1]
    raise Skip(
        "Bo'lim papkasi topilmadi (turlar/, mehmonxonalar/, joylar/, gidlar/, agentliklar/, yonalishlar/)."
    )


def _models():
    from apps.agencies.models import Agency
    from apps.catalog.models import Destination, Place
    from apps.guides.models import GuideProfile
    from apps.hotels.models import Hotel
    from apps.tours.models import Tour

    return {
        "tour": (Tour, "title"),
        "hotel": (Hotel, "name"),
        "place": (Place, "name"),
        "guide": (GuideProfile, "display_name"),
        "agency": (Agency, "name"),
        "destination": (Destination, "name"),
    }


def resolve(section: str, key: str, cache: dict):
    """Slug yoki nom bo'yicha (katta-kichik harf, apostrof va bo'shliqlar farqi hisobga olinmaydi)."""
    if section not in cache:
        model, name_field = _models()[section]
        index = {}
        for pk, slug, name in model.objects.values_list("pk", "slug", name_field):
            index.setdefault(_norm(slug), pk)
            index.setdefault(_norm(name), pk)
        cache[section] = index
    pk = cache[section].get(_norm(key))
    if pk is None:
        raise Skip(f"{SECTION_TITLE[section]} topilmadi: «{key}» (slug yoki nomini tekshiring).")
    model, _ = _models()[section]
    return model.objects.get(pk=pk)


def _validate(rule, content):
    try:
        rule(content)
    except DjangoValidationError as exc:
        raise Skip(" ".join(exc.messages)) from None


def _remember(target: str, digest: str) -> None:
    try:
        with transaction.atomic():
            MediaFingerprint.objects.create(target=target, sha1=digest)
    except IntegrityError:
        raise Skip("Bu fayl allaqachon biriktirilgan.") from None


def attach(section: str, obj, filename: str, data: bytes) -> str:
    """Faylni yozuvga biriktiradi; qisqa natija matnini qaytaradi. Muammo bo'lsa — Skip."""
    from apps.catalog.models import PlaceImage
    from apps.hotels.models import HotelImage
    from apps.tours.models import TourMedia

    ext = _ext(filename)
    content = ContentFile(data, name=filename)
    target = f"{section}:{obj.pk}"
    digest = hashlib.sha1(data).hexdigest()  # noqa: S324 — xavfsizlik emas, takrorni aniqlash

    if section in ("tour", "hotel"):
        if ext not in IMAGE_EXTS + VIDEO_EXTS:
            raise Skip(f"Faqat rasm ({', '.join(IMAGE_EXTS)}) yoki video ({', '.join(VIDEO_EXTS)}).")
        _validate(media_rule, content)
        kind = media_kind(filename)
        gallery = obj.media.all() if section == "tour" else obj.images.all()
        try:
            check_gallery_limit(gallery, kind)
        except DjangoValidationError as exc:
            raise Skip(" ".join(exc.messages)) from None
        _remember(target, digest)
        cover = kind == "image" and not gallery.filter(is_cover=True).exists()
        model, field = (TourMedia, "file") if section == "tour" else (HotelImage, "image")
        item = model(**{section: obj}, kind=kind, is_cover=cover, sort_order=gallery.count())
        getattr(item, field).save(filename, content, save=False)
        item.save()
        return "muqova" if cover else ("video" if kind == "video" else "galereya")

    if section == "place":
        if ext in AUDIO_EXTS:
            _validate(obj._meta.get_field("audio_guide").validators[0], content)
            _remember(target, digest)
            obj.audio_guide.save(filename, content)
            return "audio-gid"
        if ext not in IMAGE_EXTS:
            raise Skip("Joy uchun rasm yoki audio (mp3, m4a, ogg).")
        _validate(image_rule, content)
        _remember(target, digest)
        if not obj.cover_image:
            obj.cover_image.save(filename, content)
            return "muqova"
        item = PlaceImage(place=obj, sort_order=obj.images.count())
        item.image.save(filename, content, save=False)
        item.save()
        return "galereya"

    # Bitta rasm: gid surati, agentlik logotipi, yo'nalish muqovasi — yangisi eskisini almashtiradi
    if ext not in IMAGE_EXTS:
        raise Skip(f"Faqat rasm: {', '.join(IMAGE_EXTS)}.")
    _validate(image_rule, content)
    _remember(target, digest)
    field = {"guide": "photo", "agency": "logo", "destination": "cover_image"}[section]
    getattr(obj, field).save(filename, content)
    return {"guide": "surat", "agency": "logotip", "destination": "muqova"}[section]


def process_batch(job_id: int, *, batch: int = BATCH) -> MediaImportJob | None:
    """Navbatdagi `batch` ta fayl. Boshqa jarayon shu ishni qilayotgan bo'lsa — hech narsa qilmaydi."""
    with transaction.atomic():
        job = (
            MediaImportJob.objects.select_for_update(skip_locked=True)
            .filter(pk=job_id, status__in=[MediaImportJob.Status.QUEUED, MediaImportJob.Status.RUNNING])
            .first()
        )
        if job is None:
            return None
        try:
            with job.file.open("rb") as fh, zipfile.ZipFile(fh) as zf:
                names = media_entries(zf)
                cache: dict = {}
                report = list(job.report)
                for path in names[job.processed : job.processed + batch]:
                    row = {"path": path, "ok": False, "target": "", "message": ""}
                    try:
                        section, key, filename = parse_path(path)
                        obj = resolve(section, key, cache)
                        row["target"] = f"{SECTION_TITLE[section]}: {obj}"
                        with transaction.atomic():
                            row["message"] = attach(section, obj, filename, zf.read(path))
                        row["ok"] = True
                        job.attached += 1
                    except Skip as exc:
                        row["message"] = str(exc)
                    report.append(row)
                    job.processed += 1
        except (OSError, zipfile.BadZipFile) as exc:
            job.status, job.error, job.finished_at = (
                MediaImportJob.Status.FAILED,
                f"ZIP o'qilmadi: {exc}",
                timezone.now(),
            )
            job.save()
            return job
        job.report = report
        job.total = len(names)
        if job.processed >= job.total:
            job.status, job.finished_at = MediaImportJob.Status.DONE, timezone.now()
        else:
            job.status = MediaImportJob.Status.RUNNING
        job.save()
    if job.status == MediaImportJob.Status.DONE and job.file:
        job.file.delete(save=True)  # ZIP endi kerak emas
    return job


def process_pending(*, seconds: float = 20) -> int:
    """Scheduler: navbatdagi ishlarni vaqt chegarasigacha ishlaydi. Nechta qism bajarilganini qaytaradi."""
    import time

    start, done = time.monotonic(), 0
    for job_id in MediaImportJob.objects.filter(
        status__in=[MediaImportJob.Status.QUEUED, MediaImportJob.Status.RUNNING]
    ).values_list("pk", flat=True):
        while time.monotonic() - start < seconds:
            job = process_batch(job_id)
            if job is None:
                break
            done += 1
            if job.status != MediaImportJob.Status.RUNNING:
                break
    return done
