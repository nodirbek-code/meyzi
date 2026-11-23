"""Fayllar: yopiq saqlash (faqat admin) va yuklash cheklovlari."""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db.models.fields.files import FieldFile
from django.utils.deconstruct import deconstructible

MB = 1024 * 1024
IMAGE_EXTS = ("jpg", "jpeg", "png", "webp")
VIDEO_EXTS = ("mp4", "mov", "webm")
DOC_EXTS = ("pdf", "jpg", "jpeg", "png")


class PrivateStorage(FileSystemStorage):
    """MEDIA'dan tashqarida — veb orqali berilmaydi.

    `url()` faqat admin yuklab olish sahifasiga olib boradi.
    """

    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT  # har safar o'qiladi (testlarda override ishlashi uchun)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        from django.urls import reverse

        return reverse("private-file", args=[name])


def private_storage():
    """Yopiq fayllar: `CLOUDINARY_URL` bo'lsa — Cloudinary (authenticated), aks holda — PRIVATE_MEDIA_ROOT."""
    if getattr(settings, "CLOUDINARY_URL", ""):
        from .cloud_storage import CloudinaryStorage

        return CloudinaryStorage(private=True)
    return PrivateStorage()


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


# ---------- Faylning haqiqiy formati (kengaytma emas, ichidagi baytlar) ----------

# Pillow formati → ruxsat etilgan kengaytmalar
_IMAGE_FORMATS = {"JPEG": ("jpg", "jpeg"), "PNG": ("png",), "WEBP": ("webp",)}


def _head(f, n: int = 64) -> bytes:
    pos = f.tell() if hasattr(f, "tell") else 0
    try:
        f.seek(0)
        return f.read(n) or b""
    finally:
        f.seek(pos)


def sniff_image(f) -> str | None:
    """Haqiqiy rasm bo'lsa — Pillow formati (JPEG/PNG/WEBP), aks holda None."""
    from PIL import Image, UnidentifiedImageError

    pos = f.tell() if hasattr(f, "tell") else 0
    try:
        f.seek(0)
        with Image.open(f) as img:
            fmt = img.format
            img.verify()  # buzilgan / soxta fayl — xato
        return fmt
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        return None
    finally:
        f.seek(pos)


def sniff_video(f) -> str | None:
    """mp4/mov (ISO BMFF: 4–8 baytda `ftyp`) yoki webm (EBML sarlavhasi)."""
    head = _head(f, 16)
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "mov" if head[8:10] == b"qt" else "mp4"
    if head.startswith(bytes.fromhex("1a45dfa3")):  # EBML
        return "webm"
    return None


def is_pdf(f) -> bool:
    return _head(f, 5) == b"%PDF-"


@deconstructible
class FileRule:
    """Hajm, kengaytma va haqiqiy format cheklovi (model va serializer validatori).

    `kind`: "image" | "video" | "document" | "media" (rasm yoki video) | "" (faqat kengaytma — masalan audio).
    """

    def __init__(self, max_mb: int, exts: tuple[str, ...], label: str, kind: str = ""):
        self.max_mb, self.exts, self.label, self.kind = max_mb, exts, label, kind

    def __call__(self, f):
        if isinstance(f, FieldFile) and f._committed:
            # Allaqachon saqlangan fayl (tahrirlashda o'zgarmagan) — qayta tekshirilmaydi: Cloudinary'dan
            # yuklab olish shart emas, fayl yo'qolgan bo'lsa ham boshqa maydonlarni saqlash mumkin
            return
        ext = _ext(f.name)
        if ext not in self.exts:
            raise ValidationError(f"{self.label}: faqat {', '.join(self.exts)} formatlari.")
        if f.size and f.size > self.max_mb * MB:
            raise ValidationError(f"{self.label}: fayl hajmi {self.max_mb} MB dan oshmasin.")
        if not self.kind or not hasattr(f, "seek"):
            return
        if ext in IMAGE_EXTS and self.kind in ("image", "media", "document"):
            fmt = sniff_image(f)
            if fmt is None or ext not in _IMAGE_FORMATS.get(fmt, ()):
                raise ValidationError(f"{self.label}: fayl haqiqiy {ext.upper()} rasm emas yoki buzilgan.")
        elif ext in VIDEO_EXTS and self.kind in ("video", "media"):
            if sniff_video(f) is None or (ext == "webm") != (sniff_video(f) == "webm"):
                raise ValidationError(f"{self.label}: fayl haqiqiy {ext.upper()} video emas yoki buzilgan.")
        elif ext == "pdf" and self.kind == "document":
            if not is_pdf(f):
                raise ValidationError(f"{self.label}: fayl haqiqiy PDF emas.")

    def __eq__(self, other):
        return isinstance(other, FileRule) and (self.max_mb, self.exts, self.kind) == (
            other.max_mb,
            other.exts,
            other.kind,
        )


# Hamma joyda bir xil: rasm — 6 MB, video — 20 MB
IMAGE_MAX_MB = 6
VIDEO_MAX_MB = 20
# Bitta tur / mehmonxona galereyasi: 20 ta rasm, 4 ta video
MAX_IMAGES = 20
MAX_VIDEOS = 4

image_rule = FileRule(IMAGE_MAX_MB, IMAGE_EXTS, "Rasm", "image")
video_rule = FileRule(VIDEO_MAX_MB, VIDEO_EXTS, "Video", "video")
media_rule = FileRule(VIDEO_MAX_MB, IMAGE_EXTS + VIDEO_EXTS, "Fayl", "media")
document_rule = FileRule(IMAGE_MAX_MB, DOC_EXTS, "Hujjat", "document")


def media_kind(name: str) -> str:
    """Kengaytma bo'yicha: "image" | "video" | ""."""
    ext = _ext(name)
    return "image" if ext in IMAGE_EXTS else "video" if ext in VIDEO_EXTS else ""


def check_gallery_limit(queryset, kind: str, *, exclude_pk=None) -> None:
    """Galereyada `kind` bo'yicha chegarani tekshiradi (rasm — 20, video — 4)."""
    limit, label = (MAX_VIDEOS, "video") if kind == "video" else (MAX_IMAGES, "rasm")
    qs = queryset.filter(kind=kind)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if qs.count() >= limit:
        raise ValidationError(f"Ko'pi bilan {limit} ta {label} yuklash mumkin.")
