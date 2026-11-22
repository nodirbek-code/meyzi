from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class Review(TimeStampedModel):
    """Sharh: faqat yakunlangan (completed) bron egasi, bitta bronga bitta."""

    class Status(models.TextChoices):
        PENDING = "pending", "Tekshiruvda"
        PUBLISHED = "published", "E'lon qilingan"
        HIDDEN = "hidden", "Yashirilgan"

    booking = models.OneToOneField("bookings.Booking", on_delete=models.PROTECT, related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviews")
    tour = models.ForeignKey("tours.Tour", on_delete=models.PROTECT, related_name="reviews")
    agency = models.ForeignKey("agencies.Agency", on_delete=models.PROTECT, related_name="reviews")

    rating = models.PositiveSmallIntegerField("baho", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("matn", blank=True)
    status = models.CharField(
        "holat", max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    moderation_note = models.CharField("moderator izohi", max_length=255, blank=True)

    agency_reply = models.TextField("agentlik javobi", blank=True)
    agency_replied_at = models.DateTimeField("javob vaqti", null=True, blank=True)

    class Meta:
        verbose_name = "sharh"
        verbose_name_plural = "sharhlar"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name="review_rating_1_5")
        ]

    def __str__(self):
        return f"{self.tour} — {self.rating}★"
