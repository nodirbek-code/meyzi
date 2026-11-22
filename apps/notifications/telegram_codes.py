"""
Telefon raqamini tasdiqlash kodini Telegram orqali yuborish (Telegram Gateway API).

Kod to'g'ridan-to'g'ri shu telefon raqamiga ulangan Telegram akkauntiga keladi — foydalanuvchi
botga kirishi shart emas. Hujjat: https://core.telegram.org/gateway/api

TELEGRAM_CODE_BACKEND:
- console — kod server logiga chiqadi (dev)
- locmem  — testlar uchun (`outbox` ro'yxatiga yoziladi)
- gateway — haqiqiy yuborish (TELEGRAM_GATEWAY_TOKEN kerak)
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

log = logging.getLogger("meyzi.telegram_codes")

GATEWAY_URL = "https://gatewayapi.telegram.org/sendVerificationMessage"
TIMEOUT = 10

outbox: list[tuple[str, str]] = []


class CodeDeliveryError(Exception):
    pass


def send_code(phone: str, code: str, *, ttl_seconds: int) -> None:
    """`phone` — E.164 (+998XXXXXXXXX). Yuborib bo'lmasa — CodeDeliveryError."""
    backend = settings.TELEGRAM_CODE_BACKEND
    if backend == "console":
        log.warning("Telegram kod → %s: %s", phone, code)
        print(f"[TELEGRAM KOD] {phone}: {code}", flush=True)
        return
    if backend == "locmem":
        outbox.append((phone, code))
        return
    if backend == "gateway":
        _gateway_send(phone, code, ttl_seconds)
        return
    raise CodeDeliveryError(f"Noma'lum TELEGRAM_CODE_BACKEND={backend}")


def _gateway_send(phone: str, code: str, ttl_seconds: int) -> None:
    token = settings.TELEGRAM_GATEWAY_TOKEN
    if not token:
        raise CodeDeliveryError("TELEGRAM_GATEWAY_TOKEN sozlanmagan")
    payload = {
        "phone_number": phone,
        "code": code,
        "ttl": max(30, min(3600, ttl_seconds)),  # Gateway chegarasi: 30–3600 s
    }
    req = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            error = json.loads(exc.read().decode()).get("error", "")
        except Exception:
            error = ""
        raise CodeDeliveryError(f"HTTP {exc.code}: {error}") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise CodeDeliveryError(f"Tarmoq xatosi: {exc}") from None
    if not body.get("ok"):
        raise CodeDeliveryError(body.get("error") or "Noma'lum xato")
    log.info("Telegram kod yuborildi → %s (request_id=%s)", phone, body.get("result", {}).get("request_id"))
