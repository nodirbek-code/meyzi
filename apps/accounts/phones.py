import re

from rest_framework.exceptions import ValidationError

# O'zbekiston mobil raqamlari: +998 XX XXX XX XX
UZ_PHONE_RE = re.compile(r"^\+998\d{9}$")


def normalize_phone(raw: str) -> str:
    """'90 123 45 67', '+998 (90) 123-45-67', '998901234567' → '+998901234567'."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 9:
        digits = "998" + digits
    phone = "+" + digits
    if not UZ_PHONE_RE.match(phone):
        raise ValidationError({"phone": "Telefon raqami noto'g'ri. Namuna: +998 90 123 45 67"})
    return phone
