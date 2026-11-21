"""
Telefon raqamlari: format (+998 qotirilgan) va "raqam haqiqatan shu odamniki" tekshiruvi.

Raqam faqat Telegram'ga yuborilgan kod to'g'ri kiritilgandan keyin qabul qilinadi:
`POST /auth/phone-check/send-code/` → `POST /auth/phone-check/verify/` → `phone_token`.
Formalar telefon bilan birga `phone_token` yuboradi. Akkauntdagi tasdiqlangan raqam uchun token shart emas.
"""

import re

from django.conf import settings
from django.core import signing
from rest_framework.exceptions import ValidationError

# O'zbekiston raqamlari: +998 XX XXX XX XX
UZ_PHONE_RE = re.compile(r"^\+998\d{9}$")
ALLOWED_CHARS_RE = re.compile(r"^[\d\s()+\-]*$")
INVALID_TEXT = "Telefon raqami noto'g'ri. +998 dan keyin 9 ta raqam yozing, masalan: +998 90 123 45 67"
NOT_VERIFIED_TEXT = "Telefon raqami tasdiqlanmagan. Telegram'ga yuborilgan kod bilan tasdiqlang."

TOKEN_SALT = "lazuri.accounts.phone-token"


def normalize_phone(raw: str, field: str = "phone") -> str:
    """'90 123 45 67', '+998 (90) 123-45-67', '998901234567' → '+998901234567'.

    Harf va boshqa belgilar — xato.
    """
    raw = (raw or "").strip()
    if not ALLOWED_CHARS_RE.match(raw):
        raise ValidationError({field: INVALID_TEXT})
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 9:
        digits = "998" + digits
    phone = "+" + digits
    if not UZ_PHONE_RE.match(phone):
        raise ValidationError({field: INVALID_TEXT})
    return phone


def make_phone_token(phone: str) -> str:
    return signing.dumps({"p": phone}, salt=TOKEN_SALT, compress=True)


def phone_from_token(token: str) -> str | None:
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=settings.LAZURI_PHONE_TOKEN_MAX_AGE)
    except signing.BadSignature:  # muddati o'tgani (SignatureExpired) ham shu
        return None
    return data.get("p") if isinstance(data, dict) else None


def verified_phone(raw: str, token: str = "", *, user=None, field: str = "phone") -> str:
    """Format + raqam kod bilan tasdiqlangani. Normallashgan raqamni qaytaradi."""
    phone = normalize_phone(raw, field)
    if user is not None and getattr(user, "is_authenticated", False):
        if user.phone == phone and user.phone_verified:
            return phone
    if token and phone_from_token(token) == phone:
        return phone
    raise ValidationError({field: NOT_VERIFIED_TEXT})


def apply_verified_phone(attrs: dict, field: str, *, user=None, instance=None, allow_blank=False) -> dict:
    """Serializer `validate()` uchun: `attrs[field]` + `attrs["phone_token"]` → tasdiqlangan raqam.

    Tahrirlashda raqam o'zgarmagan bo'lsa, qayta tasdiqlash so'ralmaydi.
    """
    token = attrs.pop("phone_token", "") or ""
    if field not in attrs:
        return attrs
    if allow_blank and not (attrs[field] or "").strip():
        attrs[field] = ""
        return attrs
    current = getattr(instance, field, "") if instance is not None else ""
    if current:
        try:
            if normalize_phone(attrs[field], field) == current:
                attrs[field] = current
                return attrs
        except ValidationError:
            pass
    attrs[field] = verified_phone(attrs[field], token, user=user, field=field)
    return attrs


class VerifiedPhoneMixin:
    """Serializer mixin: `verified_phone_field` dagi raqam Telegram kodi bilan tasdiqlangan bo'lishi shart.

    Serializerga `phone_token = phone_token_field()` qo'shing; request — `context["request"]` dan.
    """

    verified_phone_field = "phone"
    verified_phone_allow_blank = False

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        return apply_verified_phone(
            attrs,
            self.verified_phone_field,
            user=getattr(request, "user", None),
            instance=getattr(self, "instance", None),
            allow_blank=self.verified_phone_allow_blank,
        )
