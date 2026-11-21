"""
Google (Gmail) orqali kirish.

Frontend Google Identity Services tugmasi orqali ID token (`credential`) oladi va backendga yuboradi.
Token Google'ning rasmiy tokeninfo endpoint'ida tekshiriladi: imzo, muddat, `aud` (bizning client ID),
`iss` va `email_verified`.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework.exceptions import APIException, ValidationError

from .models import User

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
TIMEOUT = 10
INVALID = "Google orqali kirib bo'lmadi. Qayta urinib ko'ring."


class GoogleNotConfigured(APIException):
    status_code = 503
    default_detail = "Google orqali kirish hozircha sozlanmagan."
    default_code = "google_not_configured"


class GoogleUnavailable(APIException):
    status_code = 503
    default_detail = "Google bilan bog'lanib bo'lmadi. Birozdan keyin qayta urinib ko'ring."
    default_code = "google_unavailable"


def is_enabled() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID)


def fetch_token_info(credential: str) -> dict:
    """Google tokeninfo javobi (dict). Token yaroqsiz bo'lsa — ValidationError."""
    url = f"{TOKENINFO_URL}?{urllib.parse.urlencode({'id_token': credential})}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code < 500:
            raise ValidationError({"credential": INVALID}) from None
        raise GoogleUnavailable() from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise GoogleUnavailable() from None


def check_claims(info: dict) -> dict:
    if info.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise ValidationError({"credential": INVALID})
    if info.get("iss") not in ISSUERS:
        raise ValidationError({"credential": INVALID})
    try:
        if int(info.get("exp", 0)) < time.time():
            raise ValidationError({"credential": INVALID})
    except (TypeError, ValueError):
        raise ValidationError({"credential": INVALID}) from None
    if not info.get("sub") or not info.get("email"):
        raise ValidationError({"credential": INVALID})
    if str(info.get("email_verified")).lower() != "true":
        raise ValidationError({"credential": "Google akkauntingizdagi email tasdiqlanmagan."})
    return info


def login(credential: str) -> tuple[User, bool]:
    """ID token → (user, yangi_mi).

    Akkaunt: avval Google ID bo'yicha, so'ng email bo'yicha, bo'lmasa yaratiladi.
    """
    if not is_enabled():
        raise GoogleNotConfigured()
    info = check_claims(fetch_token_info(credential))
    return _user_for(sub=info["sub"], email=info["email"].strip().lower(), info=info)


@transaction.atomic
def _user_for(*, sub: str, email: str, info: dict) -> tuple[User, bool]:
    from .auth_services import logout_everywhere

    user = User.objects.select_for_update().filter(google_sub=sub).first()
    created = False
    if user is None:
        user = User.objects.select_for_update().filter(email__iexact=email).first()
        if user is not None:
            if user.google_sub and user.google_sub != sub:
                raise ValidationError({"credential": "Bu email boshqa Google akkauntiga ulangan."})
            fields = ["google_sub", "email_verified"]
            if not user.email_verified:
                # Email tasdiqlanmagan akkauntni kimdir boshqa odamning emailida ochgan bo'lishi mumkin:
                # endi egasi Google bilan isbotladi — begona parol va sessiyalar bekor qilinadi.
                user.set_unusable_password()
                fields.append("password")
                logout_everywhere(user)
            user.google_sub = sub
            user.email_verified = True
            user.save(update_fields=fields)
        else:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        first_name=(info.get("given_name") or "")[:100],
                        last_name=(info.get("family_name") or "")[:100],
                        email_verified=True,
                        google_sub=sub,
                    )
                created = True
            except IntegrityError:  # parallel so'rov yaratib ulgurdi
                user = User.objects.get(google_sub=sub)
    if not user.is_active:
        raise ValidationError({"detail": "Akkaunt bloklangan."})
    return user, created
