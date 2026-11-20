from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


def default_commission():
    return settings.LAZURI_DEFAULT_COMMISSION_PERCENT


class Agency(TimeStampedModel):
    """Tur o'tkazuvchi tashkilot. LAZURI'ning o'zi ham agentlik sifatida (is_platform=True) tur yaratadi."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        SUSPENDED = "suspended", "To'xtatilgan"

    name = models.CharField("nomi", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True)
    logo = models.ImageField("logotip", upload_to="agencies/", blank=True)
    description = models.TextField("tavsif", blank=True)
    phone = models.CharField("telefon", max_length=30, blank=True)
    email = models.EmailField("email", blank=True)
    telegram = models.CharField("telegram", max_length=100, blank=True)
    website = models.URLField("sayt", blank=True)
    address = models.CharField("manzil", max_length=255, blank=True)
    inn = models.CharField("STIR (INN)", max_length=20, blank=True)
    license_number = models.CharField("litsenziya raqami", max_length=100, blank=True)

    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_verified = models.BooleanField("tekshirilgan", default=False)
    is_platform = models.BooleanField(
        "LAZURI'ning o'zi", default=False, help_text="Platformaning o'z turlari uchun agentlik"
    )
    auto_publish = models.BooleanField(
        "turlarni moderatsiyasiz e'lon qilish",
        default=False,
        help_text="O'chiq bo'lsa, agentlik turlari admin tasdig'idan keyin chiqadi",
    )
    commission_percent = models.DecimalField(
        "LAZURI komissiyasi (%)",
        max_digits=5,
        decimal_places=2,
        default=default_commission,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )

    # Keshlangan reyting (sharhlar bosqichida yangilanadi)
    rating = models.DecimalField("reyting", max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField("sharhlar soni", default=0)

    class Meta:
        verbose_name = "turagentlik"
        verbose_name_plural = "turagentliklar"
        ordering = ["-is_platform", "name"]

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class AgencyMember(TimeStampedModel):
    """Agentlik xodimi. Bitta foydalanuvchi — bitta agentlik."""

    class Role(models.TextChoices):
        OWNER = "owner", "Egasi"
        MANAGER = "manager", "Menejer"

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="members")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agency_membership"
    )
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.MANAGER)

    class Meta:
        verbose_name = "agentlik xodimi"
        verbose_name_plural = "agentlik xodimlari"

    def __str__(self):
        return f"{self.user} → {self.agency}"


class AgencyApplication(TimeStampedModel):
    """Agentlikning platformaga qo'shilish arizasi.

    Onboarding (TripHub kabi 3 qadam): ariza → tekshiruv (24 soat) → faol agentlik.
    """

    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        IN_REVIEW = "in_review", "Ko'rib chiqilmoqda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    agency_name = models.CharField("agentlik nomi", max_length=200)
    contact_person = models.CharField("mas'ul shaxs", max_length=200)
    phone = models.CharField("telefon", max_length=30)
    email = models.EmailField("email", blank=True)
    message = models.TextField("izoh", blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agency_applications",
        verbose_name="ariza bergan foydalanuvchi",
    )

    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.NEW)
    admin_note = models.TextField("admin izohi", blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="ko'rib chiqqan",
    )
    reviewed_at = models.DateTimeField("ko'rib chiqilgan vaqt", null=True, blank=True)
    agency = models.OneToOneField(
        Agency, on_delete=models.SET_NULL, null=True, blank=True, related_name="application"
    )

    class Meta:
        verbose_name = "agentlik arizasi"
        verbose_name_plural = "agentlik arizalari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agency_name} ({self.get_status_display()})"
