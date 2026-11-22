import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import LAT_VALIDATORS, LNG_VALIDATORS
from apps.core.files import document_rule, image_rule, private_storage
from apps.core.models import TimeStampedModel

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_guide_booking_code():
    return "LG" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


def default_guide_commission():
    return settings.MEYZI_GUIDE_COMMISSION_PERCENT


class SpokenLanguage(models.TextChoices):
    """Gid gapiradigan tillar (platforma interfeysi tillaridan farqli)."""

    UZ = "uz", "O'zbek"
    RU = "ru", "Rus"
    EN = "en", "Ingliz"
    DE = "de", "Nemis"
    FR = "fr", "Fransuz"
    ES = "es", "Ispan"
    IT = "it", "Italyan"
    TR = "tr", "Turk"
    ZH = "zh", "Xitoy"
    JA = "ja", "Yapon"
    KO = "ko", "Koreys"
    AR = "ar", "Arab"


class Specialization(models.TextChoices):
    HISTORY = "history", "Tarix va me'morchilik"
    CITY = "city", "Shahar sayohati"
    MOUNTAIN = "mountain", "Tog' va trekking"
    NATURE = "nature", "Tabiat"
    FOOD = "food", "Milliy taomlar"
    CRAFT = "craft", "Hunarmandchilik"
    RELIGIOUS = "religious", "Ziyorat"
    PHOTO = "photo", "Fotosayohat"


class GuideProfile(TimeStampedModel):
    """Individual gid. Ariza → MEYZI tekshiruvi (48 soat) → approved."""

    class Status(models.TextChoices):
        PENDING = "pending", "Tekshiruvda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"
        SUSPENDED = "suspended", "To'xtatilgan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_profile"
    )
    slug = models.SlugField("slug", max_length=120, unique=True)
    display_name = models.CharField("ism (ko'rinadigan)", max_length=150)
    photo = models.ImageField("rasm", upload_to="guides/", blank=True, validators=[image_rule])
    bio = models.TextField("o'zi haqida", blank=True)
    phone = models.CharField("telefon", max_length=30)
    languages = models.JSONField("tillar", default=list, help_text="SpokenLanguage kodlari")
    specializations = models.JSONField("ixtisosliklar", default=list, blank=True)
    destinations = models.ManyToManyField(
        "catalog.Destination", related_name="guides", verbose_name="shaharlar"
    )
    experience_years = models.PositiveSmallIntegerField("tajriba (yil)", default=0)

    certificate_number = models.CharField("sertifikat raqami", max_length=100, blank=True)
    certificate_file = models.FileField(
        "sertifikat (fayl)",
        upload_to="guides/certificates/",
        blank=True,
        storage=private_storage,
        validators=[document_rule],
    )
    is_certified = models.BooleanField("sertifikat tasdiqlangan", default=False)

    price_half_day_uzs = models.PositiveIntegerField("yarim kun (4 soat), so'm")
    price_full_day_uzs = models.PositiveIntegerField("to'liq kun (8 soat), so'm")
    price_per_day_uzs = models.PositiveIntegerField("ko'p kunlik, 1 kun uchun, so'm")
    group_surcharge_percent = models.PositiveSmallIntegerField(
        "guruh ustamasi (%)", default=20, validators=[MaxValueValidator(100)]
    )
    max_group_size = models.PositiveSmallIntegerField(
        "guruhdagi maks. odam", default=10, validators=[MinValueValidator(1), MaxValueValidator(50)]
    )

    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.PENDING)
    moderation_note = models.TextField("moderator izohi", blank=True)
    approved_at = models.DateTimeField("tasdiqlangan", null=True, blank=True)
    commission_percent = models.DecimalField(
        "Platforma komissiyasi (%)", max_digits=5, decimal_places=2, default=default_guide_commission
    )

    rating = models.DecimalField("reyting", max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField("sharhlar soni", default=0)
    warnings_count = models.PositiveSmallIntegerField("ogohlantirishlar", default=0)
    no_show_count = models.PositiveSmallIntegerField("kelmay qolishlar", default=0)

    class Meta:
        verbose_name = "gid"
        verbose_name_plural = "gidlar"
        ordering = ["-rating", "display_name"]

    def __str__(self):
        return self.display_name

    @property
    def is_approved(self) -> bool:
        return self.status == self.Status.APPROVED


class GuideMeetingPoint(TimeStampedModel):
    """Gid belgilagan uchrashuv joyi. Turist bron qilganda faqat shu ro'yxatdan tanlaydi (erkin matn emas)."""

    guide = models.ForeignKey(GuideProfile, on_delete=models.CASCADE, related_name="meeting_points")
    destination = models.ForeignKey(
        "catalog.Destination",
        on_delete=models.PROTECT,
        related_name="guide_meeting_points",
        verbose_name="shahar",
    )
    name = models.CharField("nomi", max_length=150, help_text="Masalan: Registon maydoni, asosiy kirish")
    address = models.CharField("manzil", max_length=255)
    latitude = models.DecimalField("kenglik", max_digits=9, decimal_places=6, validators=LAT_VALIDATORS)
    longitude = models.DecimalField("uzunlik", max_digits=9, decimal_places=6, validators=LNG_VALIDATORS)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        verbose_name = "uchrashuv joyi"
        verbose_name_plural = "uchrashuv joylari"
        ordering = ["destination_id", "name"]
        constraints = [
            models.UniqueConstraint(fields=["guide", "destination", "name"], name="uniq_guide_meeting_point")
        ]

    def __str__(self):
        return f"{self.name} — {self.address}"

    @property
    def as_text(self) -> str:
        return f"{self.name}, {self.address}"


class GuideUnavailableDate(models.Model):
    """Gid ishlamaydigan kun (o'zi belgilaydi)."""

    guide = models.ForeignKey(GuideProfile, on_delete=models.CASCADE, related_name="unavailable_dates")
    date = models.DateField("sana")
    note = models.CharField("izoh", max_length=200, blank=True)

    class Meta:
        verbose_name = "band kun"
        verbose_name_plural = "band kunlar"
        ordering = ["date"]
        constraints = [models.UniqueConstraint(fields=["guide", "date"], name="uniq_guide_unavailable_date")]

    def __str__(self):
        return f"{self.guide} — {self.date}"


class GuideBooking(TimeStampedModel):
    """
    Gidni bron qilish: turist so'rov yuboradi → gid 24 soatda qabul qiladi →
    to'lov (hozircha admin belgilaydi) → confirmed → completed.
    Narx va komissiya so'rov paytida qotiriladi.
    """

    class Duration(models.TextChoices):
        HALF_DAY = "half_day", "Yarim kun (4 soat)"
        FULL_DAY = "full_day", "To'liq kun (8 soat)"
        MULTI_DAY = "multi_day", "Ko'p kunlik"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Gid javobi kutilmoqda"
        ACCEPTED = "accepted", "Gid qabul qildi — to'lov kutilmoqda"
        CONFIRMED = "confirmed", "Tasdiqlangan (to'langan)"
        COMPLETED = "completed", "Yakunlangan"
        DECLINED = "declined", "Gid rad etdi"
        EXPIRED = "expired", "Gid javob bermadi"
        CANCELLED = "cancelled", "Bekor qilingan"

    class CancelledBy(models.TextChoices):
        TOURIST = "tourist", "Turist"
        GUIDE = "guide", "Gid"
        ADMIN = "admin", "Administrator"

    class NoShow(models.TextChoices):
        NONE = "", "—"
        TOURIST = "tourist", "Turist kelmadi"
        GUIDE = "guide", "Gid kelmadi"

    # Gid kunini band qiladigan holatlar
    ACTIVE_STATUSES = (Status.REQUESTED, Status.ACCEPTED, Status.CONFIRMED)

    code = models.CharField(
        "bron raqami", max_length=12, unique=True, default=generate_guide_booking_code, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="guide_bookings",
        verbose_name="turist",
    )
    guide = models.ForeignKey(
        GuideProfile, on_delete=models.PROTECT, related_name="bookings", verbose_name="gid"
    )
    destination = models.ForeignKey(
        "catalog.Destination", on_delete=models.PROTECT, related_name="guide_bookings", verbose_name="shahar"
    )

    duration = models.CharField("davomiylik", max_length=20, choices=Duration.choices)
    start_date = models.DateField("sana")
    days = models.PositiveSmallIntegerField("kunlar", default=1)
    start_time = models.TimeField("boshlanish vaqti")
    starts_at = models.DateTimeField("boshlanish")
    group_size = models.PositiveSmallIntegerField("odamlar soni")
    language = models.CharField("til", max_length=5, choices=SpokenLanguage.choices)

    unit_price_uzs = models.PositiveIntegerField("narx birligi (so'm)")
    base_uzs = models.PositiveBigIntegerField("asosiy narx (so'm)")
    surcharge_uzs = models.PositiveBigIntegerField("guruh ustamasi (so'm)", default=0)
    total_uzs = models.PositiveBigIntegerField("jami (so'm)")
    commission_percent = models.DecimalField("komissiya (%)", max_digits=5, decimal_places=2)
    commission_uzs = models.PositiveBigIntegerField("Platforma komissiyasi (so'm)")
    guide_amount_uzs = models.PositiveBigIntegerField("gidga (so'm)")

    meeting_place = models.ForeignKey(
        GuideMeetingPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        verbose_name="uchrashuv joyi (ro'yxatdan)",
    )
    meeting_point = models.CharField("uchrashuv joyi", max_length=255, help_text="Bron paytidagi nusxa")
    meeting_latitude = models.DecimalField(
        "uchrashuv kengligi", max_digits=9, decimal_places=6, null=True, blank=True
    )
    meeting_longitude = models.DecimalField(
        "uchrashuv uzunligi", max_digits=9, decimal_places=6, null=True, blank=True
    )
    note = models.TextField("izoh", blank=True)
    contact_name = models.CharField("aloqa uchun ism", max_length=200)
    contact_phone = models.CharField("telefon", max_length=30)

    status = models.CharField(
        "holat", max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    respond_by = models.DateTimeField("gid javob berish muddati", null=True, blank=True)
    accepted_at = models.DateTimeField("qabul qilingan", null=True, blank=True)
    confirmed_at = models.DateTimeField("to'langan", null=True, blank=True)
    decline_reason = models.TextField("rad etish sababi", blank=True)
    cancelled_at = models.DateTimeField("bekor qilingan", null=True, blank=True)
    cancelled_by = models.CharField("kim bekor qildi", max_length=20, choices=CancelledBy.choices, blank=True)
    cancel_reason = models.TextField("bekor qilish sababi", blank=True)
    refund_uzs = models.PositiveBigIntegerField("turistga qaytariladi (so'm)", default=0)
    no_show = models.CharField("kelmay qolish", max_length=10, choices=NoShow.choices, blank=True, default="")
    guide_penalty_usd = models.DecimalField("gidga jarima ($)", max_digits=6, decimal_places=2, default=0)
    guide_warnings = models.PositiveSmallIntegerField("gidga ogohlantirish", default=0)

    class Meta:
        verbose_name = "gid broni"
        verbose_name_plural = "gid bronlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["guide", "status", "start_date"])]

    def __str__(self):
        return f"{self.code} — {self.guide}"

    @property
    def end_date(self):
        from datetime import timedelta

        return self.start_date + timedelta(days=self.days - 1)


class GuideReview(TimeStampedModel):
    booking = models.OneToOneField(GuideBooking, on_delete=models.PROTECT, related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="guide_reviews")
    guide = models.ForeignKey(GuideProfile, on_delete=models.PROTECT, related_name="reviews")
    rating = models.PositiveSmallIntegerField("baho", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("matn", blank=True)
    is_published = models.BooleanField("e'lon qilingan", default=True)
    guide_reply = models.TextField("gid javobi", blank=True)

    class Meta:
        verbose_name = "gid sharhi"
        verbose_name_plural = "gid sharhlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.guide} — {self.rating}★"
