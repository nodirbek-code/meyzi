from django.db import models

from apps.core.models import TimeStampedModel


class TelegramMessage(TimeStampedModel):
    """
    Adminlarga Telegram xabari (outbox). Hodisa paytida yoziladi, `scheduler` yuboradi —
    Telegram sekin yoki ishlamay qolsa ham sayt so'rovlari kutib qolmaydi, xabar qayta yuboriladi.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Navbatda"
        SENT = "sent", "Yuborildi"
        FAILED = "failed", "Xato"

    MAX_ATTEMPTS = 5

    event = models.CharField("hodisa", max_length=50, db_index=True)
    chat_id = models.CharField("chat ID", max_length=50)
    text = models.TextField("matn")
    status = models.CharField(
        "holat", max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    attempts = models.PositiveSmallIntegerField("urinishlar", default=0)
    sent_at = models.DateTimeField("yuborilgan", null=True, blank=True)
    error = models.TextField("xato", blank=True)

    class Meta:
        verbose_name = "Telegram xabari"
        verbose_name_plural = "Telegram xabarlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} → {self.chat_id} ({self.get_status_display()})"


class UserMessage(TimeStampedModel):
    """Foydalanuvchiga email yoki SMS (outbox). Tasdiqlash kodlari darhol, qolganlari scheduler orqali."""

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        PENDING = "pending", "Navbatda"
        SENT = "sent", "Yuborildi"
        FAILED = "failed", "Xato"

    MAX_ATTEMPTS = 5

    channel = models.CharField("kanal", max_length=10, choices=Channel.choices)
    event = models.CharField("hodisa", max_length=50, db_index=True)
    recipient = models.CharField("kimga", max_length=254)
    subject = models.CharField("mavzu", max_length=200, blank=True)
    body = models.TextField("matn")
    status = models.CharField(
        "holat", max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    attempts = models.PositiveSmallIntegerField("urinishlar", default=0)
    sent_at = models.DateTimeField("yuborilgan", null=True, blank=True)
    error = models.TextField("xato", blank=True)

    class Meta:
        verbose_name = "email / SMS"
        verbose_name_plural = "email / SMS xabarlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_channel_display()} → {self.recipient} ({self.event})"
