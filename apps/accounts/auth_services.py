"""Kod bilan bog'liq auth oqimlari: parolni tiklash, email tasdiqlash, telefon orqali kirish.

Telefon kodlari SMS bilan emas — Telegram orqali yuboriladi (`apps.notifications.telegram_codes`).
"""

import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.notifications import services as notify
from apps.notifications import telegram_codes

from . import otp
from .models import OneTimeCode, User
from .phones import make_phone_token

P = OneTimeCode.Purpose
log = logging.getLogger("lazuri.auth")


class CodeNotDelivered(APIException):
    status_code = 503
    default_detail = (
        "Kodni Telegram'ga yuborib bo'lmadi. Shu raqamda Telegram ochilganini tekshiring "
        "yoki birozdan keyin qayta urinib ko'ring."
    )
    default_code = "code_not_delivered"


def _send_email_code(email: str, code: str, purpose: str):
    subjects = {
        P.EMAIL_VERIFY: ("LAZURI — emailni tasdiqlash", "Emailingizni tasdiqlash kodi"),
        P.PASSWORD_RESET: ("LAZURI — parolni tiklash", "Parolni tiklash kodi"),
    }
    subject, title = subjects[purpose]
    body = (
        f"{title}: {code}\n\n"
        "Kod 10 daqiqa amal qiladi. "
        "Agar bu so'rovni siz yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring.\n\n"
        "— LAZURI"
    )
    notify.queue_email(email, subject, body, event=purpose, immediate=True)


def _send_phone_code(purpose: str, target: str, phone: str) -> None:
    """Kod yaratadi va Telegram orqali `phone` ga yuboradi. Yuborilmasa — kod bekor qilinadi (503)."""
    code = otp.issue(purpose, target)
    try:
        telegram_codes.send_code(phone, code, ttl_seconds=settings.LAZURI_OTP_TTL_MINUTES * 60)
    except telegram_codes.CodeDeliveryError as exc:
        log.warning("Telegram kod yuborilmadi (%s): %s", phone, exc)
        # yetkazilmagan kod "qayta yuborish — 60 s" cheklovini yoqmasin
        OneTimeCode.objects.filter(purpose=purpose, target=target, used_at__isnull=True).delete()
        raise CodeNotDelivered() from None


# ---------- Email ----------


def send_email_verification(user: User) -> None:
    if not user.email:
        raise ValidationError({"detail": "Akkauntda email yo'q."})
    if user.email_verified:
        raise ValidationError({"detail": "Email allaqachon tasdiqlangan."})
    code = otp.issue(P.EMAIL_VERIFY, user.email)
    _send_email_code(user.email, code, P.EMAIL_VERIFY)


def verify_email(user: User, code: str) -> User:
    otp.verify(P.EMAIL_VERIFY, user.email or "", code)
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    return user


# ---------- Parolni tiklash ----------


def request_password_reset(email: str) -> None:
    """Foydalanuvchi bor-yo'qligini oshkor qilmaydi: javob doim bir xil."""
    email = email.strip().lower()
    if User.objects.filter(email__iexact=email, is_active=True).exists():
        code = otp.issue(P.PASSWORD_RESET, email)
        _send_email_code(email, code, P.PASSWORD_RESET)


def reset_password(email: str, code: str, new_password: str) -> User:
    from django.contrib.auth import password_validation

    email = email.strip().lower()
    otp.verify(P.PASSWORD_RESET, email, code)
    user = User.objects.get(email__iexact=email)
    password_validation.validate_password(new_password, user)
    with transaction.atomic():
        user.set_password(new_password)
        user.email_verified = True  # kod emailga keldi — demak email egasi
        user.save(update_fields=["password", "email_verified"])
        logout_everywhere(user)
    return user


def logout_everywhere(user: User) -> None:
    """Barcha refresh tokenlarni bekor qiladi (parol tiklanganda)."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


# ---------- Telefon ----------


def request_phone_login(phone: str) -> None:
    _send_phone_code(P.PHONE_LOGIN, phone, phone)


def verify_phone_login(phone: str, code: str, first_name: str = "") -> tuple[User, bool]:
    """To'g'ri kod → shu raqamli foydalanuvchi (yo'q bo'lsa yaratiladi). (user, yangi_mi)."""
    otp.verify(P.PHONE_LOGIN, phone, code)
    user = User.objects.filter(phone=phone).first()
    created = False
    if user is None:
        try:
            user = User.objects.create_user(
                email=None, phone=phone, first_name=first_name, phone_verified=True
            )
            created = True
        except IntegrityError:  # parallel so'rov yaratib ulgurdi
            user = User.objects.get(phone=phone)
    if not user.is_active:
        raise ValidationError({"detail": "Akkaunt bloklangan."})
    if not user.phone_verified:
        user.phone_verified = True
        user.save(update_fields=["phone_verified"])
    return user, created


def request_phone_change(user: User, phone: str) -> None:
    if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
        raise ValidationError({"phone": "Bu raqam boshqa akkauntga ulangan."})
    _send_phone_code(P.PHONE_CHANGE, f"{user.pk}:{phone}", phone)


def verify_phone_change(user: User, phone: str, code: str) -> User:
    otp.verify(P.PHONE_CHANGE, f"{user.pk}:{phone}", code)
    if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
        raise ValidationError({"phone": "Bu raqam boshqa akkauntga ulangan."})
    user.phone = phone
    user.phone_verified = True
    user.save(update_fields=["phone", "phone_verified"])
    return user


# ---------- Formadagi telefonni tasdiqlash (bron, arizalar, profillar) ----------


def request_phone_check(phone: str) -> None:
    _send_phone_code(P.PHONE_CONFIRM, phone, phone)


def verify_phone_check(phone: str, code: str, user: User | None = None) -> str:
    """To'g'ri kod → `phone_token` (formaga telefon bilan birga yuboriladi).

    Kirgan foydalanuvchining akkauntida telefon yo'q bo'lsa — raqam akkauntga ham ulanadi.
    """
    otp.verify(P.PHONE_CONFIRM, phone, code)
    if user is not None and user.is_authenticated and not user.phone:
        if not User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
            user.phone = phone
            user.phone_verified = True
            user.save(update_fields=["phone", "phone_verified"])
    return make_phone_token(phone)
