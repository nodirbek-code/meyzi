"""
SMS yuborish. Provayder (Eskiz, Playmobile...) bilan shartnoma bo'lgach, shu yerga backend qo'shiladi
va SMS_BACKEND sozlamasi bilan tanlanadi. Hozircha:

- console — matn server logiga chiqadi (dev; kodni log'dan ko'rasiz)
- locmem  — testlar uchun (`outbox` ro'yxatiga yoziladi)
- disabled — SMS yuborilmaydi (xabar "xato" bo'lib qoladi)
"""

import logging

from django.conf import settings

log = logging.getLogger("meyzi.sms")

outbox: list[tuple[str, str]] = []


class SmsError(Exception):
    pass


def is_enabled() -> bool:
    return settings.SMS_BACKEND != "disabled"


def send(phone: str, text: str) -> None:
    backend = settings.SMS_BACKEND
    if backend == "console":
        log.warning("SMS → %s: %s", phone, text)
        print(f"[SMS] {phone}: {text}", flush=True)
        return
    if backend == "locmem":
        outbox.append((phone, text))
        return
    raise SmsError(f"SMS provayderi sozlanmagan (SMS_BACKEND={backend})")
