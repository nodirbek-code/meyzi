"""
Telegram bot orqali ro'yxatdan o'tish (saytga kirish esa — telefon raqam + parol yoki Google).

Ro'yxatdan o'tish oqimi:
1. Saytda "Telegram orqali ro'yxatdan o'tish" → `t.me/<bot>?start=login`.
2. Bot telefon raqamini so'raydi ("Raqamni yuborish" tugmasi — Telegram kontakti).
3. Yangi foydalanuvchidan ism-familiyani so'raydi.
4. Parol o'rnatishni so'raydi va uni qayta kiritishni so'raydi (ikkalasi mos kelishi shart).
5. Foydalanuvchi bazaga yoziladi (bor bo'lsa — Telegram akkaunti unga ulanadi va parol o'rnatiladi).
6. Bot bir martalik havola yuboradi (`<sayt>/auth/telegram?code=...`) — shu zahoti saytga kirib olish uchun.
   Keyingi safar foydalanuvchi saytga telefon raqam + parol bilan kiradi (`POST /auth/phone/login/`).

Parolni unutganlar botga /parol yozadi — raqam Telegram orqali tasdiqlangani uchun yangi parol o'rnatiladi.

Parol xavfsizligi:
- Telegram chatida kiritilayotgan matnni yulduzcha bilan berkitib bo'lmaydi, shuning uchun bot parol
  xabarini qabul qilgan zahoti chatdan o'chiradi (`deleteMessage`).
- Bazada parol faqat xesh ko'rinishida (Django `make_password`): suhbat qadamida ham, foydalanuvchida ham.
- Parol matni log'ga yozilmaydi.

Raqam faqat kontakt tugmasi orqali qabul qilinadi va `contact.user_id == from.id` tekshiriladi:
shunda raqam aynan shu Telegram akkauntiniki ekanini Telegram o'zi kafolatlaydi
(qo'lda yozilgan yoki boshqa odamning kontakti qabul qilinmaydi).

Yangilanishlar: dev — `manage.py telegram_bot` (long polling), prod — webhook (`TelegramWebhookView`).
"""

import hashlib
import logging
import re
import secrets
import urllib.parse
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.notifications import telegram

from .models import TelegramBotSession, TelegramLoginLink, TelegramPhoneLink, User
from .phones import normalize_phone

log = logging.getLogger("meyzi.telegram_bot")
Step = TelegramBotSession.Step

NAME_RE = re.compile(r"^[^\W\d_]+(?:[\s'’`\-][^\W\d_]+)*$")
LINK_INVALID = "Havola yaroqsiz yoki muddati o'tgan. Saytga telefon raqam va parolingiz bilan kiring."
BLOCKED = "Akkauntingiz bloklangan. Savollar bo'lsa, qo'llab-quvvatlash xizmatiga yozing."
PASSWORD_MAX = 128

CONTACT_KEYBOARD = {
    "keyboard": [[{"text": "📱 Telefon raqamni yuborish", "request_contact": True}]],
    "resize_keyboard": True,
    "one_time_keyboard": True,
}
REMOVE_KEYBOARD = {"remove_keyboard": True}


# ---------- Bir martalik kirish havolalari ----------


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_login_link(user: User, *, is_new: bool = False) -> str:
    """Yangi havola tokeni (foydalanuvchining eski ishlatilmagan havolalari bekor bo'ladi)."""
    now = timezone.now()
    token = secrets.token_urlsafe(32)
    TelegramLoginLink.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
    TelegramLoginLink.objects.create(
        user=user,
        token_hash=_hash(token),
        is_new_user=is_new,
        expires_at=now + timedelta(minutes=settings.MEYZI_TELEGRAM_LOGIN_TTL_MINUTES),
    )
    return token


def login_url(token: str) -> str:
    return f"{settings.MEYZI_FRONTEND_URL}/auth/telegram?{urllib.parse.urlencode({'code': token})}"


@transaction.atomic
def exchange_login_link(token: str) -> tuple[User, bool]:
    """Havola tokeni → (user, yangi_mi). Token bir marta ishlaydi."""
    now = timezone.now()
    link = (
        TelegramLoginLink.objects.select_for_update()
        .select_related("user")
        .filter(token_hash=_hash(str(token).strip()), used_at__isnull=True, expires_at__gt=now)
        .first()
    )
    if link is None:
        raise ValidationError({"code": LINK_INVALID})
    link.used_at = now
    link.save(update_fields=["used_at"])
    if not link.user.is_active:
        raise ValidationError({"detail": "Akkaunt bloklangan."})
    return link.user, link.is_new_user


# ---------- "Telefon raqam qo'shish" havolalari (masalan Google orqali kirganlar uchun) ----------

PHONE_LINK_PREFIX = "phone_"
PHONE_LINK_INVALID = (
    "Havola yaroqsiz yoki muddati o'tgan. "
    "Saytda <b>Profil → Telefon raqam qo'shish</b> tugmasini qayta bosing."
)


def issue_phone_link(user: User) -> str:
    """Bot uchun bir martalik token (foydalanuvchining eski ishlatilmagan havolalari bekor bo'ladi)."""
    now = timezone.now()
    token = secrets.token_urlsafe(24)  # 32 belgi: A-Z a-z 0-9 _ - (Telegram start parametri uchun yaroqli)
    TelegramPhoneLink.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
    TelegramPhoneLink.objects.create(
        user=user,
        token_hash=_hash(token),
        expires_at=now + timedelta(minutes=settings.MEYZI_TELEGRAM_LOGIN_TTL_MINUTES),
    )
    return token


def phone_link_url(token: str) -> str:
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={PHONE_LINK_PREFIX}{token}"


# ---------- Bot xabarlari ----------


def _send(chat_id: int, text: str, markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if markup:
        payload["reply_markup"] = markup
    telegram.call("sendMessage", payload)


def _delete(chat_id: int, message_id: int | None) -> None:
    """Foydalanuvchi yozgan xabarni (parolni) chatdan o'chiradi. Bo'lmasa ham suhbat davom etadi."""
    if not message_id:
        return
    try:
        telegram.call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except telegram.TelegramError as exc:
        log.warning("Parol xabari o'chirilmadi (chat %s): %s", chat_id, exc)


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _site_login_url() -> str:
    return f"{settings.MEYZI_FRONTEND_URL}/login"


def _send_with_button(chat_id: int, text: str, button: str, url: str) -> None:
    """Havola tugmasi bilan xabar; localhost'da (Telegram tugmani qabul qilmaydi) — havola matnda."""
    if telegram.is_public_url(url):
        try:
            _send(chat_id, text, {"inline_keyboard": [[{"text": button, "url": url}]]})
            return
        except telegram.TelegramError as exc:
            log.warning("Havola tugmasi yuborilmadi, matn sifatida yuboriladi: %s", exc)
    _send(chat_id, f'{text}\n\n<a href="{_esc(url)}">{_esc(url)}</a>')


def _send_login_link(chat_id: int, user: User, *, is_new: bool, intro: str) -> None:
    url = login_url(issue_login_link(user, is_new=is_new))
    ttl = settings.MEYZI_TELEGRAM_LOGIN_TTL_MINUTES
    phone = _esc(user.phone or "")
    text = (
        f"{intro}\n\nKeyingi safar saytga <b>{phone}</b> raqami va parolingiz bilan kirasiz.\n"
        "Hozir esa quyidagi tugma orqali darhol kirishingiz mumkin "
        f"({ttl} daqiqa amal qiladi, bir marta ishlaydi)."
    )
    _send_with_button(chat_id, text, f"🌐 {settings.BRAND_NAME} saytiga o'tish", url)


def _send_already_registered(chat_id: int, user: User) -> None:
    name = _esc(user.first_name or "do'stim")
    text = (
        f"Xush kelibsiz, {name}! Siz allaqachon ro'yxatdan o'tgansiz.\n\n"
        f"Saytga <b>{_esc(user.phone or '')}</b> raqami va parolingiz bilan kiring.\n"
        "Parolni unutgan bo'lsangiz — /parol buyrug'ini yuboring."
    )
    _send_with_button(chat_id, text, f"🌐 {settings.BRAND_NAME} saytiga kirish", _site_login_url())


def _ask_contact(chat_id: int, text: str | None = None) -> None:
    _send(
        chat_id,
        text
        or (
            f"Assalomu alaykum! <b>{settings.BRAND_NAME}</b> saytida ro'yxatdan o'tish uchun "
            "telefon raqamingizni yuboring — pastdagi tugmani bosing."
        ),
        CONTACT_KEYBOARD,
    )


def _ask_name(chat_id: int, tg_user: dict) -> None:
    suggestion = " ".join(filter(None, [tg_user.get("first_name"), tg_user.get("last_name")])).strip()
    markup = REMOVE_KEYBOARD
    if suggestion and NAME_RE.match(suggestion):
        markup = {
            "keyboard": [[{"text": suggestion[:100]}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
    _send(chat_id, "Rahmat! Endi ism va familiyangizni yozing.\nMasalan: <i>Aziz Karimov</i>", markup)


def _ask_password(chat_id: int, intro: str = "") -> None:
    _send(
        chat_id,
        (f"{intro}\n\n" if intro else "")
        + "🔐 Saytga kirish uchun <b>parol o'rnating</b> va shu yerga yozing.\n"
        "Kamida 8 ta belgi, faqat raqamlardan iborat bo'lmasin.\n\n"
        "<i>Xavfsizlik uchun parolingiz yuborilgan zahoti chatdan o'chiriladi va hech kim "
        "(hatto biz ham) uni ko'ra olmaydi.</i>",
        REMOVE_KEYBOARD,
    )


# ---------- Foydalanuvchini yozish ----------


def parse_full_name(text: str) -> tuple[str, str] | None:
    name = " ".join((text or "").split())
    if not (2 <= len(name) <= 150) or not NAME_RE.match(name):
        return None
    # "nodir zarifboyev" → "Nodir Zarifboyev" (qolgan harflar o'zgarmaydi: "McDonald" buzilmaydi)
    name = " ".join(w[:1].upper() + w[1:] for w in name.split(" "))
    first, _, last = name.partition(" ")
    return first[:100], last[:100]


@transaction.atomic
def register_user(
    telegram_id: int,
    phone: str,
    first_name: str = "",
    last_name: str = "",
    password_hash: str = "",
) -> tuple[User, bool]:
    """Raqam bo'yicha foydalanuvchi (yo'q bo'lsa yaratiladi) va unga Telegram akkaunti ulanadi.

    Raqam — asosiy identifikator (saytdagi "telefon + parol" bilan kirish shu akkauntga).
    `password_hash` berilsa — u akkaunt paroli bo'ladi (raqam Telegram orqali tasdiqlangan).
    Shu Telegram akkaunti boshqa (eski raqamli) akkauntga ulangan bo'lsa — u yerdan uziladi.
    """
    User.objects.filter(telegram_id=telegram_id).exclude(phone=phone).update(telegram_id=None)
    user = User.objects.select_for_update().filter(phone=phone).first()
    if user is None:
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=None,
                    phone=phone,
                    phone_verified=True,
                    first_name=first_name,
                    last_name=last_name,
                    telegram_id=telegram_id,
                )
                if password_hash:
                    user.password = password_hash
                    user.save(update_fields=["password"])
            return user, True
        except IntegrityError:  # parallel so'rov yaratib ulgurdi
            user = User.objects.select_for_update().get(phone=phone)
    fields = []
    if user.telegram_id != telegram_id:
        user.telegram_id = telegram_id
        fields.append("telegram_id")
    if not user.phone_verified:
        user.phone_verified = True
        fields.append("phone_verified")
    if first_name and not user.first_name:
        user.first_name, user.last_name = first_name, last_name or user.last_name
        fields += ["first_name", "last_name"]
    if password_hash:
        user.password = password_hash
        fields.append("password")
    if fields:
        user.save(update_fields=fields)
    return user, False


def _finish(chat_id: int, tg_user: dict, session: TelegramBotSession) -> None:
    telegram_id = tg_user["id"]
    user, created = register_user(
        telegram_id, session.phone, session.first_name, session.last_name, session.password_hash
    )
    TelegramBotSession.objects.filter(telegram_id=telegram_id).delete()
    if not user.is_active:
        _send(chat_id, BLOCKED, REMOVE_KEYBOARD)
        return
    name = _esc(user.first_name or "do'stim")
    if created:
        intro = f"✅ Tabriklaymiz, {name}! Siz {settings.BRAND_NAME} saytida ro'yxatdan o'tdingiz."
    else:
        intro = f"✅ Parol o'rnatildi, {name}! Akkauntingiz Telegram'ga ulandi."
    _send_login_link(chat_id, user, is_new=created, intro=intro)


def _start_password_step(chat_id: int, user: User, intro: str) -> None:
    TelegramBotSession.objects.update_or_create(
        telegram_id=user.telegram_id,
        defaults={
            "step": Step.PASSWORD,
            "phone": user.phone,
            "first_name": "",
            "last_name": "",
            "password_hash": "",
        },
    )
    _ask_password(chat_id, intro)


# ---------- Yangilanishlarni qayta ishlash ----------


def _linked_user(tg_user: dict) -> User | None:
    user = User.objects.filter(telegram_id=tg_user["id"]).first()
    return user if user is not None and user.phone else None


def _on_start(chat_id: int, tg_user: dict, payload: str = "") -> None:
    user = _linked_user(tg_user)
    if user is not None:
        TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).delete()
        if not user.is_active:
            _send(chat_id, BLOCKED)
            return
        name = _esc(user.first_name or "do'stim")
        if payload == "parol":
            _start_password_step(chat_id, user, f"{name}, yangi parol o'rnatamiz.")
        elif user.has_usable_password():
            _send_already_registered(chat_id, user)
        else:  # parolsiz eski akkaunt — endi saytga parol bilan kiriladi
            _start_password_step(chat_id, user, f"Xush kelibsiz, {name}!")
        return
    TelegramBotSession.objects.update_or_create(
        telegram_id=tg_user["id"],
        defaults={"step": Step.CONTACT, "phone": "", "first_name": "", "last_name": "", "password_hash": ""},
    )
    _ask_contact(chat_id)


def _on_reset_password(chat_id: int, tg_user: dict) -> None:
    """/parol — parolni unutganlar uchun: Telegram'ga ulangan akkauntga yangi parol."""
    user = _linked_user(tg_user)
    if user is None:
        _on_start(chat_id, tg_user)
        return
    if not user.is_active:
        _send(chat_id, BLOCKED)
        return
    name = _esc(user.first_name or "do'stim")
    _start_password_step(chat_id, user, f"{name}, yangi parol o'rnatamiz.")


def _on_contact(chat_id: int, tg_user: dict, contact: dict) -> None:
    if contact.get("user_id") != tg_user["id"]:
        _ask_contact(chat_id, "Iltimos, <b>o'zingizning</b> raqamingizni pastdagi tugma orqali yuboring.")
        return
    try:
        phone = normalize_phone(contact.get("phone_number", ""))
    except ValidationError:
        _send(
            chat_id,
            "Kechirasiz, hozircha faqat O'zbekiston raqamlari (+998) bilan ro'yxatdan o'tish mumkin.",
            REMOVE_KEYBOARD,
        )
        TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).delete()
        return
    existing = User.objects.filter(phone=phone).first()
    if existing is not None and not existing.is_active:
        TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).delete()
        _send(chat_id, BLOCKED, REMOVE_KEYBOARD)
        return
    if existing is not None and existing.first_name:
        if existing.has_usable_password():
            # Raqam egasi ekani Telegram orqali tasdiqlandi — akkauntga ulaymiz, parol o'zgarmaydi
            user, _ = register_user(tg_user["id"], phone)
            TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).delete()
            _send(chat_id, "✅ Raqam tasdiqlandi, akkauntingiz Telegram'ga ulandi.", REMOVE_KEYBOARD)
            _send_already_registered(chat_id, user)
            return
        TelegramBotSession.objects.update_or_create(
            telegram_id=tg_user["id"],
            defaults={
                "step": Step.PASSWORD,
                "phone": phone,
                "first_name": "",
                "last_name": "",
                "password_hash": "",
            },
        )
        _ask_password(chat_id, f"Raqam tasdiqlandi, {_esc(existing.first_name)}!")
        return
    TelegramBotSession.objects.update_or_create(
        telegram_id=tg_user["id"], defaults={"step": Step.NAME, "phone": phone, "password_hash": ""}
    )
    _ask_name(chat_id, tg_user)


def _on_phone_link_start(chat_id: int, tg_user: dict, token: str) -> None:
    """ "Telefon raqam qo'shish" havolasi: foydalanuvchini token orqali taniymiz, faqat raqam so'raymiz."""
    now = timezone.now()
    with transaction.atomic():
        link = (
            TelegramPhoneLink.objects.select_for_update()
            .select_related("user")
            .filter(token_hash=_hash(token.strip()), used_at__isnull=True, expires_at__gt=now)
            .first()
        )
        if link is None:
            _send(chat_id, PHONE_LINK_INVALID, REMOVE_KEYBOARD)
            return
        user = link.user
        link.used_at = now
        link.save(update_fields=["used_at"])
    if not user.is_active:
        _send(chat_id, BLOCKED, REMOVE_KEYBOARD)
        return
    if user.phone and user.phone_verified:
        _send(chat_id, f"Akkauntingizda raqam allaqachon bor: <b>{_esc(user.phone)}</b>.", REMOVE_KEYBOARD)
        return
    if User.objects.filter(telegram_id=tg_user["id"]).exclude(pk=user.pk).exists():
        _send(
            chat_id,
            f"Bu Telegram akkaunt boshqa {settings.BRAND_NAME} akkauntiga ulangan. "
            "O'sha akkauntga telefon raqam va parol bilan kiring "
            "yoki boshqa Telegram akkauntdan foydalaning.",
            REMOVE_KEYBOARD,
        )
        return
    TelegramBotSession.objects.update_or_create(
        telegram_id=tg_user["id"],
        defaults={
            "step": Step.LINK_PHONE,
            "link_user": user,
            "phone": "",
            "first_name": "",
            "last_name": "",
            "password_hash": "",
        },
    )
    name = _esc(user.first_name or "do'stim")
    account = f" (<b>{_esc(user.email)}</b>)" if user.email else ""
    _send(
        chat_id,
        f"Assalomu alaykum, {name}! {settings.BRAND_NAME} akkauntingizga{account} "
        "telefon raqam qo'shamiz.\n\n"
        "Pastdagi <b>📱 Telefon raqamni yuborish</b> tugmasini bosing.",
        CONTACT_KEYBOARD,
    )


def _on_link_phone_contact(chat_id: int, tg_user: dict, session: TelegramBotSession, contact: dict) -> None:
    if contact.get("user_id") != tg_user["id"]:
        _send(
            chat_id,
            "Iltimos, <b>o'zingizning</b> raqamingizni pastdagi tugma orqali yuboring.",
            CONTACT_KEYBOARD,
        )
        return
    try:
        phone = normalize_phone(contact.get("phone_number", ""))
    except ValidationError:
        TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).delete()
        _send(
            chat_id,
            "Kechirasiz, hozircha faqat O'zbekiston raqamlari (+998) qabul qilinadi.",
            REMOVE_KEYBOARD,
        )
        return
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=session.link_user_id).first()
        TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).delete()
        if user is None or not user.is_active:
            _send(chat_id, BLOCKED if user else PHONE_LINK_INVALID, REMOVE_KEYBOARD)
            return
        if user.phone and user.phone_verified:
            _send(
                chat_id, f"Akkauntingizda raqam allaqachon bor: <b>{_esc(user.phone)}</b>.", REMOVE_KEYBOARD
            )
            return
        if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
            _send(
                chat_id,
                f"<b>{_esc(phone)}</b> raqami boshqa {settings.BRAND_NAME} akkauntiga tegishli. "
                "Saytga shu raqam va parolingiz bilan kiring (parolni unutgan bo'lsangiz — /parol).",
                REMOVE_KEYBOARD,
            )
            return
        if User.objects.filter(telegram_id=tg_user["id"]).exclude(pk=user.pk).exists():
            _send(chat_id, "Bu Telegram akkaunt boshqa akkauntga ulangan.", REMOVE_KEYBOARD)
            return
        user.phone, user.phone_verified, user.telegram_id = phone, True, tg_user["id"]
        try:
            with transaction.atomic():
                user.save(update_fields=["phone", "phone_verified", "telegram_id"])
        except IntegrityError:  # parallel so'rov shu raqamni band qilib ulgurdi
            _send(chat_id, "Bu raqam boshqa akkauntga tegishli.", REMOVE_KEYBOARD)
            return
    _send(chat_id, f"✅ Raqam akkauntingizga qo'shildi: <b>{_esc(phone)}</b>", REMOVE_KEYBOARD)
    _send_with_button(
        chat_id,
        "Saytdagi profilingizni yangilang. "
        "Parol bilan ham kirmoqchi bo'lsangiz — /parol buyrug'ini yuboring.",
        f"🌐 {settings.BRAND_NAME}: profilga qaytish",
        f"{settings.MEYZI_FRONTEND_URL}/account/profile",
    )


def _on_name(chat_id: int, session: TelegramBotSession, text: str) -> None:
    parsed = parse_full_name(text)
    if parsed is None:
        _send(chat_id, "Ism-familiyani harflar bilan yozing. Masalan: <i>Aziz Karimov</i>")
        return
    session.first_name, session.last_name = parsed
    session.step = Step.PASSWORD
    session.save(update_fields=["first_name", "last_name", "step", "updated_at"])
    _ask_password(chat_id, f"Rahmat, {_esc(session.first_name)}!")


def _password_errors(password: str, session: TelegramBotSession) -> list[str]:
    if len(password) > PASSWORD_MAX:
        return [f"Parol {PASSWORD_MAX} belgidan oshmasin."]
    if any(ch.isspace() for ch in password):
        return ["Parolda bo'sh joy bo'lmasin."]
    # O'xshashlik tekshiruvi uchun bazaga yozilmaydigan vaqtinchalik foydalanuvchi
    probe = User(phone=session.phone, first_name=session.first_name, last_name=session.last_name)
    try:
        password_validation.validate_password(password, probe)
    except DjangoValidationError as exc:
        return list(exc.messages)
    return []


def _on_password(chat_id: int, session: TelegramBotSession, text: str, message_id: int | None) -> None:
    _delete(chat_id, message_id)
    errors = _password_errors(text, session)
    if errors:
        _send(
            chat_id,
            "❌ Bu parol mos emas:\n• " + "\n• ".join(_esc(e) for e in errors) + "\n\nBoshqa parol yozing.",
        )
        return
    session.password_hash = make_password(text)
    session.step = Step.PASSWORD2
    session.save(update_fields=["password_hash", "step", "updated_at"])
    _send(chat_id, "✅ Qabul qilindi (xabaringiz o'chirildi).\n\nEndi parolni <b>yana bir bor</b> yozing.")


def _on_password2(
    chat_id: int, tg_user: dict, session: TelegramBotSession, text: str, message_id: int | None
) -> None:
    _delete(chat_id, message_id)
    if not session.password_hash or not check_password(text, session.password_hash):
        session.password_hash = ""
        session.step = Step.PASSWORD
        session.save(update_fields=["password_hash", "step", "updated_at"])
        _send(chat_id, "❌ Parollar mos kelmadi. Parolni boshidan yozing.")
        return
    _finish(chat_id, tg_user, session)


HELP = (
    "Ro'yxatdan o'tish uchun /start, parolni unutgan bo'lsangiz — /parol buyrug'ini yuboring.\n"
    "Saytga telefon raqam va parolingiz bilan kirasiz."
)


def handle_update(update: dict) -> None:
    """Telegram'dan kelgan bitta yangilanish (faqat shaxsiy chatdagi xabarlar)."""
    message = update.get("message")
    if not message or message.get("chat", {}).get("type") != "private":
        return
    tg_user = message.get("from") or {}
    if not tg_user.get("id") or tg_user.get("is_bot"):
        return
    chat_id = message["chat"]["id"]
    message_id = message.get("message_id")
    raw_text = message.get("text") or ""
    text = raw_text.strip()
    parts = text.split()
    command = parts[0].split("@")[0].lower() if text.startswith("/") else ""

    arg = parts[1] if len(parts) > 1 else ""
    if command in {"/start", "/login"} and arg.startswith(PHONE_LINK_PREFIX):
        _on_phone_link_start(
            chat_id, tg_user, arg[len(PHONE_LINK_PREFIX) :]
        )  # token katta-kichik harfga sezgir
    elif command in {"/start", "/login"}:
        _on_start(chat_id, tg_user, arg.lower())
    elif command in {"/parol", "/password"}:
        _on_reset_password(chat_id, tg_user)
    elif command == "/id":
        _send(chat_id, f"Chat ID: <code>{chat_id}</code>")
    elif message.get("contact"):
        session = TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).first()
        if session is not None and session.step == Step.LINK_PHONE:
            _on_link_phone_contact(chat_id, tg_user, session, message["contact"])
        else:
            _on_contact(chat_id, tg_user, message["contact"])
    else:
        session = TelegramBotSession.objects.filter(telegram_id=tg_user["id"]).first()
        step = session.step if session else None
        if step == Step.LINK_PHONE:
            _send(
                chat_id,
                "Raqamni pastdagi <b>📱 Telefon raqamni yuborish</b> tugmasi orqali yuboring.",
                CONTACT_KEYBOARD,
            )
        elif step == Step.NAME and text and not command:
            _on_name(chat_id, session, text)
        elif step == Step.PASSWORD and raw_text and not command:
            _on_password(chat_id, session, raw_text, message_id)
        elif step == Step.PASSWORD2 and raw_text and not command:
            _on_password2(chat_id, tg_user, session, raw_text, message_id)
        elif step in {Step.PASSWORD, Step.PASSWORD2}:
            _ask_password(chat_id)
        elif step == Step.CONTACT:
            _ask_contact(
                chat_id, "Raqamni pastdagi <b>📱 Telefon raqamni yuborish</b> tugmasi orqali yuboring."
            )
        else:
            _send(chat_id, HELP)


def process_update(update: dict) -> None:
    """`handle_update` + xatolarni log'ga yozish (bitta xabar butun botni to'xtatmasin)."""
    try:
        handle_update(update)
    except Exception:
        # Faqat update_id — xabar matnida parol bo'lishi mumkin
        log.exception("Telegram yangilanishini qayta ishlashda xato: %s", update.get("update_id"))
