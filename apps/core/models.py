from django.db import models


class TimeStampedModel(models.Model):
    """Barcha modellar uchun yaratilgan/yangilangan vaqt."""

    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        abstract = True


def local_private_storage():
    """Har doim server diski (PRIVATE_MEDIA_ROOT) — Cloudinary yoqilgan bo'lsa ham."""
    from .files import PrivateStorage

    return PrivateStorage()


class MediaImportJob(TimeStampedModel):
    """ZIP orqali ommaviy rasm/video yuklash (control → Media). Qismlab ishlanadi — `core.media_import`."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Navbatda"
        RUNNING = "running", "Ishlanmoqda"
        DONE = "done", "Tayyor"
        FAILED = "failed", "Xato"

    # ZIP serverning o'z diskida (Cloudinary emas: bepul tarifda raw fayl ≤ 10 MB); tugagach o'chiriladi
    file = models.FileField("ZIP", upload_to="imports/", storage=local_private_storage, blank=True)
    original_name = models.CharField("fayl nomi", max_length=255)
    status = models.CharField("holat", max_length=10, choices=Status.choices, default=Status.QUEUED)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="yuklagan",
    )
    total = models.PositiveIntegerField("jami fayllar", default=0)
    processed = models.PositiveIntegerField("ko'rib chiqilgan", default=0)
    attached = models.PositiveIntegerField("biriktirilgan", default=0)
    report = models.JSONField("hisobot", default=list, blank=True)  # [{"path", "ok", "target", "message"}]
    error = models.TextField("xato", blank=True)
    finished_at = models.DateTimeField("tugagan", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "media import"
        verbose_name_plural = "media importlar"

    def __str__(self):
        return f"{self.original_name} ({self.get_status_display()})"


class MediaFingerprint(models.Model):
    """Bir xil faylni bir yozuvga ikki marta biriktirmaslik uchun (ZIP qayta yuklansa)."""

    target = models.CharField(max_length=60)  # "tour:12", "hotel:3", "place:7"
    sha1 = models.CharField(max_length=40)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["target", "sha1"], name="uniq_media_fingerprint")]

    def __str__(self):
        return f"{self.target} {self.sha1[:8]}"
