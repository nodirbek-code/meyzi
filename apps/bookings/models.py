import secrets

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.tours.models import CancellationPolicy

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # chalkash belgilar (0/O, 1/I) yo'q


def generate_code():
    return "LZ" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


class Booking(TimeStampedModel):
    """
    Bron. Yaratilganda joylar `hold` muddatiga band qilinadi (pending_payment).
    To'lov o'tsa — confirmed, muddat o'tsa — expired (joylar qaytadi).
    Narx, komissiya va bekor qilish siyosati bron paytida qotiriladi.
    """

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "To'lov kutilmoqda"
        CONFIRMED = "confirmed", "Tasdiqlangan"
        CANCELLED = "cancelled", "Bekor qilingan"
        EXPIRED = "expired", "Muddati o'tgan"
        COMPLETED = "completed", "Yakunlangan"

    class CancelledBy(models.TextChoices):
        TOURIST = "tourist", "Turist"
        AGENCY = "agency", "Agentlik"
        ADMIN = "admin", "Administrator"

    # Joy band qiladigan holatlar
    ACTIVE_STATUSES = (Status.PENDING_PAYMENT, Status.CONFIRMED)

    code = models.CharField("bron raqami", max_length=12, unique=True, default=generate_code, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings", verbose_name="turist"
    )
    departure = models.ForeignKey(
        "tours.Departure", on_delete=models.PROTECT, related_name="bookings", verbose_name="jo'nash sanasi"
    )
    tour = models.ForeignKey(
        "tours.Tour", on_delete=models.PROTECT, related_name="bookings", verbose_name="tur"
    )
    agency = models.ForeignKey(
        "agencies.Agency", on_delete=models.PROTECT, related_name="bookings", verbose_name="agentlik"
    )

    seats = models.PositiveSmallIntegerField("joylar soni")
    unit_price_uzs = models.PositiveIntegerField("1 kishi narxi (so'm)")
    total_uzs = models.PositiveBigIntegerField("jami (so'm)")
    commission_percent = models.DecimalField("komissiya (%)", max_digits=5, decimal_places=2)
    commission_uzs = models.PositiveBigIntegerField("LAZURI komissiyasi (so'm)")
    agency_amount_uzs = models.PositiveBigIntegerField("agentlikka (so'm)")
    cancellation_policy = models.CharField(
        "bekor qilish siyosati", max_length=20, choices=CancellationPolicy.choices
    )
    departure_at = models.DateTimeField("jo'nash vaqti")

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
    cancel_reason = models.TextField("bekor qilish sababi", blank=True)
    refund_uzs = models.PositiveBigIntegerField("qaytariladigan summa (so'm)", default=0)

    class Meta:
        verbose_name = "bron"
        verbose_name_plural = "bronlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["agency", "status"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.tour}"

    @property
    def holds_seats(self) -> bool:
        return self.status in self.ACTIVE_STATUSES


class Traveler(models.Model):
    """Sayohatchi (ixtiyoriy) — agentlik mehmonxona/ro'yxat uchun ismlarni biladi."""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="travelers")
    full_name = models.CharField("F.I.Sh.", max_length=200)
    phone = models.CharField("telefon", max_length=30, blank=True)
    birth_date = models.DateField("tug'ilgan sana", null=True, blank=True)

    class Meta:
        verbose_name = "sayohatchi"
        verbose_name_plural = "sayohatchilar"
        ordering = ["id"]

    def __str__(self):
        return self.full_name
