"""
To'lov usullari — hozircha faqat ko'rinish uchun: barchasi "Tez kunda".

Merchant shartnomalari (Payme, Click, Uzum Nasiya) tuzilgach, shu yerda `enabled=True` qilinadi va
to'lov kodi alohida yoziladi. Logotiplar: `apps/payments/static/payments/<code>.svg` (yoki .png) —
rasmiy brend to'plamlaridan oling. Fayl bo'lmasa `logo` = null.
"""

from django.contrib.staticfiles import finders
from django.templatetags.static import static

METHODS = [
    {"code": "payme", "name": "Payme", "description": "Payme ilovasi yoki karta orqali"},
    {"code": "click", "name": "Click", "description": "Click ilovasi yoki karta orqali"},
    {"code": "uzum_nasiya", "name": "Uzum Nasiya", "description": "Muddatli to'lov — 12 oygacha"},
]

COMING_SOON = "Tez kunda"


def _logo(code: str) -> str | None:
    for ext in ("svg", "png", "webp"):
        path = f"payments/{code}.{ext}"
        if finders.find(path):
            return static(path)
    return None


def available_methods(request=None) -> list[dict]:
    result = []
    for m in METHODS:
        logo = _logo(m["code"])
        if logo and request is not None:
            logo = request.build_absolute_uri(logo)
        result.append({**m, "logo": logo, "enabled": False, "status_text": COMING_SOON})
    return result
