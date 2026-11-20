from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.files import image_rule
from apps.core.models import TimeStampedModel


class Article(TimeStampedModel):
    """Blog — "Qo'llanmalar": sayohatga tayyorgarlik maqolalari (TripHub'dagi /guides kabi)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        PUBLISHED = "published", "E'lon qilingan"

    title = models.CharField("sarlavha", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True)
    excerpt = models.CharField("qisqa mazmun", max_length=400, blank=True)
    body = models.TextField("matn", help_text="Markdown yoki oddiy matn")
    cover = models.ImageField("muqova", upload_to="articles/", blank=True, validators=[image_rule])
    destination = models.ForeignKey(
        "catalog.Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name="yo'nalish",
    )
    tours = models.ManyToManyField(
        "tours.Tour", blank=True, related_name="articles", verbose_name="bog'liq turlar"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="muallif"
    )
    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField("e'lon qilingan", null=True, blank=True)

    class Meta:
        verbose_name = "maqola"
        verbose_name_plural = "maqolalar (Qo'llanmalar)"
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class FaqItem(TimeStampedModel):
    """Savol-javob."""

    question = models.CharField("savol", max_length=300)
    answer = models.TextField("javob")
    sort_order = models.PositiveIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        verbose_name = "savol-javob"
        verbose_name_plural = "savol-javoblar (FAQ)"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question


class Page(TimeStampedModel):
    """Oddiy sahifa: foydalanish shartlari, maxfiylik siyosati, biz haqimizda..."""

    slug = models.SlugField("slug", max_length=100, unique=True, help_text="terms, privacy, about...")
    title = models.CharField("sarlavha", max_length=200)
    body = models.TextField("matn", help_text="Markdown yoki oddiy matn")
    is_published = models.BooleanField("e'lon qilingan", default=True)

    class Meta:
        verbose_name = "sahifa"
        verbose_name_plural = "sahifalar"
        ordering = ["title"]

    def __str__(self):
        return self.title
