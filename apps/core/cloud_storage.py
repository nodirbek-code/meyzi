"""Cloudinary'da fayl saqlash — Render kabi diski vaqtinchalik hostinglar uchun.

`CLOUDINARY_URL` berilsa yoqiladi (prod.py). Bazada nom avvalgidek saqlanadi:
`destinations/samarqand_ab12cd3.jpg`.
Cloudinary'dagi joyi: `<CLOUDINARY_FOLDER>/destinations/samarqand_ab12cd3` (rasm/video — kengaytmasiz,
formatni Cloudinary o'zi qo'shadi; boshqa fayllar — `raw`, kengaytma bilan).

- Rasm (jpg, png, webp) → `image`; video va audio (mp4, mov, webm, mp3, ...) → `video`
  (Cloudinary audio'ni ham shu turda saqlaydi); qolganlari → `raw`.
- `private=True` (gid sertifikatlari) → `type="authenticated"`: ochiq havola yo'q, faqat imzolangan
  havola bilan yuklab olinadi. `url()` admin yuklab olish sahifasiga olib boradi (avvalgidek).
- Har bir faylga tasodifiy qo'shimcha qo'shiladi — nom bandligini tekshirish uchun Cloudinary Admin API'ga
  (soatiga cheklangan) so'rov yuborilmaydi.
"""

import os
import urllib.error
import urllib.request
from urllib.parse import unquote, urlparse

import cloudinary
import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
import cloudinary.utils
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.crypto import get_random_string
from django.utils.deconstruct import deconstructible

from .files import IMAGE_EXTS, VIDEO_EXTS, _ext

AUDIO_EXTS = ("mp3", "m4a", "aac", "ogg", "wav")


def cloudinary_enabled() -> bool:
    return bool(getattr(settings, "CLOUDINARY_URL", ""))


def _configure() -> None:
    """SDK'ni settings.CLOUDINARY_URL dan sozlaydi (.env orqali berilsa ham ishlaydi)."""
    url = urlparse(settings.CLOUDINARY_URL)
    if url.scheme != "cloudinary" or not (url.hostname and url.username and url.password):
        raise ImproperlyConfigured(
            "CLOUDINARY_URL: cloudinary://<api_key>:<api_secret>@<cloud_name> ko'rinishida bo'lsin."
        )
    cloudinary.config(
        cloud_name=url.hostname, api_key=unquote(url.username), api_secret=unquote(url.password), secure=True
    )


@deconstructible
class CloudinaryStorage(Storage):
    def __init__(self, private: bool = False):
        self.private = private
        if cloudinary_enabled():
            _configure()

    # ---------- nom → Cloudinary ----------

    def _folder(self) -> str:
        base = getattr(settings, "CLOUDINARY_FOLDER", "meyzi").strip("/")
        return f"{base}/private" if self.private else base

    def _resource_type(self, name: str) -> str:
        if self.private:
            return "raw"  # pdf ham, rasm ham — o'zgartirishsiz, faqat yuklab olish uchun
        ext = _ext(name)
        if ext in IMAGE_EXTS:
            return "image"
        if ext in VIDEO_EXTS or ext in AUDIO_EXTS:
            return "video"
        return "raw"

    def _public_id(self, name: str) -> str:
        pid = f"{self._folder()}/{name}"
        if self._resource_type(name) != "raw":
            pid = os.path.splitext(pid)[0]
        return pid

    def _options(self, name: str) -> dict:
        return {
            "resource_type": self._resource_type(name),
            "type": "authenticated" if self.private else "upload",
        }

    def _delivery_url(self, name: str) -> str:
        opts = self._options(name)
        if opts["resource_type"] != "raw":
            opts["format"] = _ext(name)
        if self.private:
            opts["sign_url"] = True
        return cloudinary.utils.cloudinary_url(self._public_id(name), secure=True, **opts)[0]

    # ---------- Storage API ----------

    def get_available_name(self, name, max_length=None):
        root, ext = os.path.splitext(name.replace("\\", "/"))
        suffix = "_" + get_random_string(7).lower()
        if max_length is not None:
            root = root[: max(1, max_length - len(suffix) - len(ext))]
        return f"{root}{suffix}{ext}"

    def _save(self, name, content):
        if hasattr(content, "seek"):
            content.seek(0)
        cloudinary.uploader.upload(
            content,
            public_id=self._public_id(name),
            overwrite=False,
            unique_filename=False,
            use_filename=False,
            **self._options(name),
        )
        return name

    def _open(self, name, mode="rb"):
        try:
            with urllib.request.urlopen(self._delivery_url(name), timeout=30) as resp:  # noqa: S310 — https Cloudinary
                data = resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(name) from None
            raise
        f = ContentFile(data)
        f.name = name
        return f

    def delete(self, name):
        if name:
            cloudinary.uploader.destroy(self._public_id(name), invalidate=True, **self._options(name))

    def _resource(self, name):
        try:
            return cloudinary.api.resource(self._public_id(name), **self._options(name))
        except cloudinary.exceptions.NotFound:
            return None

    def exists(self, name):
        return bool(name) and self._resource(name) is not None

    def size(self, name):
        res = self._resource(name)
        if res is None:
            raise FileNotFoundError(name)
        return res.get("bytes", 0)

    def url(self, name):
        if self.private:
            from django.urls import reverse

            return reverse("private-file", args=[name])
        return self._delivery_url(name)
