"""Fayllar: yopiq saqlash (faqat admin) va yuklash cheklovlari."""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
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
    return PrivateStorage()


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


@deconstructible
class FileRule:
    """Hajm va kengaytma cheklovi (model validatori)."""

    def __init__(self, max_mb: int, exts: tuple[str, ...], label: str):
        self.max_mb, self.exts, self.label = max_mb, exts, label

    def __call__(self, f):
        if _ext(f.name) not in self.exts:
            raise ValidationError(f"{self.label}: faqat {', '.join(self.exts)} formatlari.")
        if f.size and f.size > self.max_mb * MB:
            raise ValidationError(f"{self.label}: fayl {self.max_mb} MB dan oshmasin.")

    def __eq__(self, other):
        return isinstance(other, FileRule) and (self.max_mb, self.exts) == (other.max_mb, other.exts)


image_rule = FileRule(10, IMAGE_EXTS, "Rasm")
video_rule = FileRule(100, VIDEO_EXTS, "Video")
media_rule = FileRule(100, IMAGE_EXTS + VIDEO_EXTS, "Fayl")
document_rule = FileRule(10, DOC_EXTS, "Hujjat")
