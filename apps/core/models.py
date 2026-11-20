from django.db import models


class TimeStampedModel(models.Model):
    """Barcha modellar uchun yaratilgan/yangilangan vaqt."""

    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        abstract = True
