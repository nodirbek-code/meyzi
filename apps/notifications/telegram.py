"""Telegram Bot API — minimal mijoz (stdlib, qo'shimcha paket kerak emas)."""

import json
import urllib.error
import urllib.parse
import urllib.request
from html import escape

from django.conf import settings

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 10


class TelegramError(Exception):
    pass


def is_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_IDS)


def call(method: str, payload: dict | None = None, timeout: int = TIMEOUT) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise TelegramError("TELEGRAM_BOT_TOKEN sozlanmagan")
    url = API.format(token=settings.TELEGRAM_BOT_TOKEN, method=method)
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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


def is_public_url(url: str) -> bool:
    """Telegram tugmalari localhost havolalarini qabul qilmaydi — dev'da havola matn bo'lib yuboriladi."""
    host = urllib.parse.urlparse(url).hostname or ""
    return "." in host and host not in {"127.0.0.1", "0.0.0.0"}


def send_message(chat_id: str, text: str, *, button_text: str = "", button_url: str = "") -> dict:
    """HTML xabar. `button_url` berilsa — xabar ostida havola tugmasi (localhost bo'lsa — matnda havola)."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if button_url:
        if is_public_url(button_url):
            payload["reply_markup"] = {
                "inline_keyboard": [[{"text": button_text or button_url, "url": button_url}]]
            }
        else:
            label = escape(button_text or "Havola")
            payload["text"] = f'{text}\n\n{label}: <a href="{escape(button_url)}">{escape(button_url)}</a>'
    return call("sendMessage", payload)
