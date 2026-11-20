"""Telegram Bot API — minimal mijoz (stdlib, qo'shimcha paket kerak emas)."""

import json
import urllib.error
import urllib.request

from django.conf import settings

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 10


class TelegramError(Exception):
    pass


def is_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_IDS)


def call(method: str, payload: dict | None = None) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise TelegramError("TELEGRAM_BOT_TOKEN sozlanmagan")
    url = API.format(token=settings.TELEGRAM_BOT_TOKEN, method=method)
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            description = json.loads(exc.read().decode()).get("description", "")
        except Exception:
            description = ""
        raise TelegramError(f"HTTP {exc.code}: {description}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TelegramError(f"Tarmoq xatosi: {exc}") from None
    if not body.get("ok"):
        raise TelegramError(body.get("description", "Noma'lum xato"))
    return body["result"]


def send_message(chat_id: str, text: str) -> dict:
    return call(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
    )
