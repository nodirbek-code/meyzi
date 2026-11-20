"""
Bir martalik tasdiqlash kodlari (6 raqam). Kodning o'zi bazada saqlanmaydi — faqat HMAC xeshi.

Cheklovlar: amal qilish muddati (LAZURI_OTP_TTL_MINUTES), 5 ta noto'g'ri urinish,
qayta yuborish — 60 soniyadan keyin,
bitta manzilga soatiga 5 tadan ko'p emas.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled, ValidationError

from .models import OneTimeCode

INVALID = "Kod noto'g'ri yoki muddati o'tgan."


def _hash(code: str, target: str, purpose: str) -> str:
    msg = f"{purpose}:{target}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


@transaction.atomic
def issue(purpose: str, target: str) -> str:
    """Yangi kod yaratadi (eski faol kodlar bekor bo'ladi) va kodni qaytaradi — yuborish chaqiruvchida."""
    now = timezone.now()
    recent = OneTimeCode.objects.filter(
        purpose=purpose, target=target, created_at__gte=now - timedelta(hours=1)
    )
    last = recent.order_by("-created_at").first()
    if last and (now - last.created_at).total_seconds() < settings.LAZURI_OTP_RESEND_SECONDS:
        wait = settings.LAZURI_OTP_RESEND_SECONDS - int((now - last.created_at).total_seconds())
        raise Throttled(wait=wait, detail=f"Kodni qayta so'rash uchun {wait} soniya kuting.")
    if recent.count() >= settings.LAZURI_OTP_MAX_PER_HOUR:
        raise Throttled(detail="Juda ko'p urinish. Bir soatdan keyin qayta urinib ko'ring.")

    OneTimeCode.objects.filter(purpose=purpose, target=target, used_at__isnull=True).update(used_at=now)
    code = f"{secrets.randbelow(1_000_000):06d}"
    OneTimeCode.objects.create(
        purpose=purpose,
        target=target,
        code_hash=_hash(code, target, purpose),
        expires_at=now + timedelta(minutes=settings.LAZURI_OTP_TTL_MINUTES),
    )
    return code


def verify(purpose: str, target: str, code: str) -> None:
    """To'g'ri bo'lsa kodni ishlatilgan qiladi, aks holda ValidationError.

    Urinishlar alohida tranzaksiyada saqlanadi (view `non_atomic_requests` bo'lishi shart).
    """
    now = timezone.now()
    with transaction.atomic():
        otp = (
            OneTimeCode.objects.select_for_update()
            .filter(purpose=purpose, target=target, used_at__isnull=True, expires_at__gt=now)
            .order_by("-created_at")
            .first()
        )
        if not otp or otp.attempts >= settings.LAZURI_OTP_MAX_ATTEMPTS:
            raise ValidationError({"code": INVALID})
        if not hmac.compare_digest(otp.code_hash, _hash(str(code).strip(), target, purpose)):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            ok = False
        else:
            otp.used_at = now
            otp.save(update_fields=["used_at"])
            ok = True
    if not ok:
        raise ValidationError({"code": INVALID})
