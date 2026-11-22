import secrets
from datetime import time

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import LAT_VALIDATORS, LNG_VALIDATORS
from apps.core.files import image_rule, media_rule
from apps.core.models import TimeStampedModel
from apps.tours.models import CancellationPolicy

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_hotel_booking_code():
    return "LH" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


def default_hotel_commission():
    return settings.MEYZI_HOTEL_COMMISSION_PERCENT


class Amenity(models.TextChoices):
    WIFI = "wifi", "Wi-Fi"
    PARKING = "parking", "Avtoturargoh"
    BREAKFAST = "breakfast", "Nonushta"
    AC = "ac", "Konditsioner"
    POOL = "pool", "Basseyn"
    SPA = "spa", "Spa"
    GYM = "gym", "Sport zal"
    RESTAURANT = "restaurant", "Restoran"
    TRANSFER = "transfer", "Aeroport transferi"
    PETS = "pets", "Uy hayvonlari mumkin"


class Hotel(TimeStampedModel):
    """Mehmonxona / hostel / mehmon uyi. Ariza → MEYZI tekshiruvi → approved."""

    class Status(models.TextChoices):
        PENDING = "pending", "Tekshiruvda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"
        SUSPENDED = "suspended", "To'xtatilgan"

    class Kind(models.TextChoices):
        HOTEL = "hotel", "Mehmonxona"
        HOSTEL = "hostel", "Hostel"
        GUESTHOUSE = "guesthouse", "Mehmon uyi"
        RESORT = "resort", "Dam olish maskani"

    name = models.CharField("nomi", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True)
    kind = models.CharField("turi", max_length=20, choices=Kind.choices, default=Kind.HOTEL)
    destination = models.ForeignKey(
        "catalog.Destination", on_delete=models.PROTECT, related_name="hotels", verbose_name="shahar"
    )
    stars = models.PositiveSmallIntegerField(
        "yulduz", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    description = models.TextField("tavsif", blank=True)
    address = models.CharField("manzil", max_length=255)
    latitude = models.DecimalField(
        "kenglik", max_digits=9, decimal_places=6, null=True, blank=True, validators=LAT_VALIDATORS
    )
    longitude = models.DecimalField(
        "uzunlik", max_digits=9, decimal_places=6, null=True, blank=True, validators=LNG_VALIDATORS
    )
    phone = models.CharField("telefon", max_length=30)
    email = models.EmailField("email", blank=True)
    amenities = models.JSONField("qulayliklar", default=list, blank=True)
    check_in_time = models.TimeField("kirish vaqti", default=time(14, 0))
    check_out_time = models.TimeField("chiqish vaqti", default=time(12, 0))
    cancellation_policy = models.CharField(
        "bekor qilish siyosati",
        max_length=20,
        choices=CancellationPolicy.choices,
        default=CancellationPolicy.FREE,
    )

    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.PENDING)
    moderation_note = models.TextField("moderator izohi", blank=True)
    commission_percent = models.DecimalField(
        "Platforma komissiyasi (%)", max_digits=5, decimal_places=2, default=default_hotel_commission
    )
    is_featured = models.BooleanField("tavsiya", default=False)
    rating = models.DecimalField("reyting", max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField("sharhlar soni", default=0)

    class Meta:
        verbose_name = "mehmonxona"
        verbose_name_plural = "mehmonxonalar"
        ordering = ["-is_featured", "-rating", "name"]

    def __str__(self):
        return self.name

    @property
    def is_approved(self) -> bool:
        return self.status == self.Status.APPROVED


class HotelMember(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Egasi"
        MANAGER = "manager", "Menejer"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="members")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hotel_membership"
    )
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.MANAGER)

    class Meta:
        verbose_name = "mehmonxona xodimi"
        verbose_name_plural = "mehmonxona xodimlari"

    def __str__(self):
        return f"{self.user} → {self.hotel}"


class HotelImage(models.Model):
    """Galereya: rasmlar (ko'pi bilan 20, har biri ≤ 6 MB) va videolar (ko'pi bilan 4, ≤ 20 MB)."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Rasm"
        VIDEO = "video", "Video"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="images")
    kind = models.CharField("turi", max_length=10, choices=Kind.choices, default=Kind.IMAGE)
    image = models.FileField("fayl (rasm yoki video)", upload_to="hotels/", validators=[media_rule])
    caption = models.CharField("izoh", max_length=200, blank=True)
    is_cover = models.BooleanField("muqova", default=False)
    sort_order = models.PositiveIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "rasm"
        verbose_name_plural = "rasmlar"
        ordering = ["-is_cover", "sort_order", "id"]

    def __str__(self):
        return self.caption or f"{self.hotel} rasmi"


class RoomType(TimeStampedModel):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField("nomi", max_length=150, help_text="Masalan: Standart ikki kishilik")
    description = models.TextField("tavsif", blank=True)
    capacity = models.PositiveSmallIntegerField(
        "sig'im (kishi)", validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    beds = models.CharField("karavotlar", max_length=100, blank=True, help_text="1 katta yoki 2 alohida")
    size_m2 = models.PositiveSmallIntegerField("maydon (m²)", null=True, blank=True)
    price_per_night_uzs = models.PositiveIntegerField("1 kecha narxi (so'm)")
    total_rooms = models.PositiveSmallIntegerField("xonalar soni", validators=[MinValueValidator(1)])
    amenities = models.JSONField("qulayliklar", default=list, blank=True)
    image = models.ImageField("rasm", upload_to="hotels/rooms/", blank=True, validators=[image_rule])
    is_active = models.BooleanField("sotuvda", default=True)

    class Meta:
        verbose_name = "xona turi"
        verbose_name_plural = "xona turlari"
        ordering = ["price_per_night_uzs"]

    def __str__(self):
        return f"{self.hotel} — {self.name}"


class HotelBooking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        CONFIRMED = "confirmed", "Tasdiqlangan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati o'tgan"
        COMPLETED = "completed", "Yakunlangan"

    class CancelledBy(models.TextChoices):
        TOURIST = "tourist", "Turist"
        HOTEL = "hotel", "Mehmonxona"
        ADMIN = "admin", "Administrator"

    ACTIVE_STATUSES = (Status.PENDING_PAYMENT, Status.CONFIRMED)

    code = models.CharField(
        "bron raqami", max_length=12, unique=True, default=generate_hotel_booking_code, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="hotel_bookings",
        verbose_name="turist",
    )
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name="bookings")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="bookings")

    check_in = models.DateField("kirish")
    check_out = models.DateField("chiqish")
    nights = models.PositiveSmallIntegerField("kechalar")
    rooms = models.PositiveSmallIntegerField("xonalar")
    guests = models.PositiveSmallIntegerField("mehmonlar")
    check_in_at = models.DateTimeField("kirish vaqti")

    price_per_night_uzs = models.PositiveIntegerField("1 kecha narxi (so'm)")
    total_uzs = models.PositiveBigIntegerField("jami (so'm)")
    commission_percent = models.DecimalField("komissiya (%)", max_digits=5, decimal_places=2)
    commission_uzs = models.PositiveBigIntegerField("Platforma komissiyasi (so'm)")
    hotel_amount_uzs = models.PositiveBigIntegerField("mehmonxonaga (so'm)")
    cancellation_policy = models.CharField(
        "bekor qilish siyosati", max_length=20, choices=CancellationPolicy.choices
    )

    contact_name = models.CharField("aloqa uchun ism", max_length=200)
    contact_phone = models.CharField("telefon", max_length=30)
    contact_email = models.EmailField("email", blank=True)
    note = models.TextField("izoh", blank=True)

    status = models.CharField(
        "holat", max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT, db_index=True
    )
    expires_at = models.DateTimeField("to'lov muddati", null=True, blank=True)
    confirmed_at = models.DateTimeField("tasdiqlangan", null=True, blank=True)
    cancelled_at = models.DateTimeField("bekor qilingan", null=True, blank=True)
    cancelled_by = models.CharField("kim bekor qildi", max_length=20, choices=CancelledBy.choices, blank=True)
    cancel_reason = models.TextField("sabab", blank=True)
    refund_uzs = models.PositiveBigIntegerField("qaytariladi (so'm)", default=0)

    class Meta:
        verbose_name = "mehmonxona broni"
        verbose_name_plural = "mehmonxona bronlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["room_type", "status", "check_in", "check_out"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F("check_in")), name="hotel_checkout_after_in"
            )
        ]

    def __str__(self):
        return f"{self.code} — {self.hotel}"


class HotelReview(TimeStampedModel):
    booking = models.OneToOneField(HotelBooking, on_delete=models.PROTECT, related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="hotel_reviews")
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name="reviews")
    rating = models.PositiveSmallIntegerField("baho", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("matn", blank=True)
    is_published = models.BooleanField("e'lon qilingan", default=True)
    hotel_reply = models.TextField("mehmonxona javobi", blank=True)

    class Meta:
        verbose_name = "mehmonxona sharhi"
        verbose_name_plural = "mehmonxona sharhlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.hotel} — {self.rating}★"
