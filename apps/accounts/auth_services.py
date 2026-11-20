"""Kod bilan bog'liq auth oqimlari: parolni tiklash, email tasdiqlash, telefon orqali kirish."""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.notifications import services as notify

from . import otp
from .models import OneTimeCode, User

P = OneTimeCode.Purpose


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


def _send_sms_code(phone: str, code: str, purpose: str):
    notify.queue_sms(
        phone, f"LAZURI: tasdiqlash kodi {code}. Hech kimga aytmang.", event=purpose, immediate=True
    )


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
    code = otp.issue(P.PHONE_LOGIN, phone)
    _send_sms_code(phone, code, P.PHONE_LOGIN)


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
    code = otp.issue(P.PHONE_CHANGE, f"{user.pk}:{phone}")
    _send_sms_code(phone, code, P.PHONE_CHANGE)


def verify_phone_change(user: User, phone: str, code: str) -> User:
    otp.verify(P.PHONE_CHANGE, f"{user.pk}:{phone}", code)
    if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
        raise ValidationError({"phone": "Bu raqam boshqa akkauntga ulangan."})
    user.phone = phone
    user.phone_verified = True
    user.save(update_fields=["phone", "phone_verified"])
    return user
