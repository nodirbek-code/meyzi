"""
Platforma imkoniyatlari ro'yxati — frontend nimani ko'rsatishni shu yerdan biladi.
"Tez kunda" imkoniyatlar `enabled: false` bilan keladi; kod yozilganda shu yerda yoqiladi.
"""

from django.conf import settings

COMING_SOON = "Tez kunda"


def features(request=None) -> dict:
    from apps.payments.methods import available_methods

    return {
        "languages": [{"code": code, "name": name} for code, name in settings.LANGUAGES],
        "default_language": settings.LANGUAGE_CODE,
        "ai_route": {
            "enabled": False,
            "status_text": COMING_SOON,
            "description": "Sun'iy intellekt sizning istaklaringizga qarab sayohat marshrutini tuzib beradi.",
        },
        "multilingual_content": {
            "enabled": False,
            "status_text": COMING_SOON,
            "description": "Turlar va sahifalar o'zbek, rus va ingliz tillarida.",
        },
        "payments": available_methods(request),
        # Telefon kodlari SMS emas, Telegram orqali keladi
        "phone_verification": {"channel": "telegram", "country_code": "+998", "digits": 9},
        "google_login": {
            "enabled": bool(settings.GOOGLE_CLIENT_ID),
            "client_id": settings.GOOGLE_CLIENT_ID or None,
        },
    }
