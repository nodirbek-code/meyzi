"""Telegram bot orqali ro'yxatdan o'tish va kirish (apps.accounts.telegram_bot)."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from apps.accounts import telegram_bot
from apps.accounts.models import TelegramBotSession, TelegramLoginLink, User
from apps.notifications import telegram

pytestmark = pytest.mark.django_db

TG_ID = 555000111
LOGIN = "/api/v1/auth/telegram/login/"
WEBHOOK = "/api/v1/auth/telegram/webhook/"


@pytest.fixture
def bot(settings, monkeypatch):
    """Bot yoqilgan, lekin tarmoqqa chiqmaydi — yuborilgan xabarlar ro'yxatga yoziladi."""
    settings.TELEGRAM_BOT_TOKEN = "123:TEST"
    settings.TELEGRAM_BOT_USERNAME = "meyzi_test_bot"
    settings.MEYZI_FRONTEND_URL = "https://meyzi.uz"
    sent = []

    def fake_call(method, payload=None, timeout=10):
        sent.append(payload or {})
        return {}

    monkeypatch.setattr(telegram, "call", fake_call)
    return sent


PASSWORD = "Tog'-Yo'li-2026"
PHONE_LOGIN = "/api/v1/auth/phone/login/"


def msg(text=None, contact=None, tg_id=TG_ID, chat_type="private", message_id=1):
    m = {
        "message_id": message_id,
        "chat": {"id": tg_id, "type": chat_type},
        "from": {"id": tg_id, "is_bot": False, "first_name": "Aziz", "last_name": "Karimov"},
    }
    if text is not None:
        m["text"] = text
    if contact is not None:
        m["contact"] = contact
    return {"update_id": 1, "message": m}


def contact(phone="+998901234567", user_id=TG_ID):
    return {"phone_number": phone, "first_name": "Aziz", "user_id": user_id}


def code_from(sent) -> str:
    """Oxirgi xabardagi havoladan `code` ni ajratib oladi."""
    payload = sent[-1]
    url = payload["reply_markup"]["inline_keyboard"][0][0]["url"]
    assert url.startswith("https://meyzi.uz/auth/telegram?")
    return parse_qs(urlparse(url).query)["code"][0]


def test_full_registration_flow(bot, api):
    telegram_bot.handle_update(msg("/start login"))
    assert bot[-1]["reply_markup"]["keyboard"][0][0]["request_contact"] is True

    telegram_bot.handle_update(msg(contact=contact("998 90 123 45 67")))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "name"
    assert bot[-1]["reply_markup"]["keyboard"][0][0]["text"] == "Aziz Karimov"  # Telegram ismi taklif

    telegram_bot.handle_update(msg("  aziz   Karimov "))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "password"
    assert not User.objects.exists()

    telegram_bot.handle_update(msg(PASSWORD, message_id=41))
    session = TelegramBotSession.objects.get(telegram_id=TG_ID)
    assert session.step == "password2"
    assert session.password_hash != PASSWORD and check_password(PASSWORD, session.password_hash)
    assert {"chat_id": TG_ID, "message_id": 41} in bot  # parol xabari chatdan o'chirildi

    telegram_bot.handle_update(msg(PASSWORD, message_id=42))
    assert {"chat_id": TG_ID, "message_id": 42} in bot
    user = User.objects.get(phone="+998901234567")
    assert (user.first_name, user.last_name, user.telegram_id) == ("Aziz", "Karimov", TG_ID)
    assert user.phone_verified and user.email is None and user.check_password(PASSWORD)
    assert user.password != PASSWORD
    assert not TelegramBotSession.objects.exists()
    assert not any(PASSWORD in str(p.get("text", "")) for p in bot)  # bot parolni qaytarib yozmaydi

    r = api.post(LOGIN, {"code": code_from(bot)}, format="json")
    assert r.status_code == 200, r.data
    assert r.data["is_new"] is True and r.data["access"] and r.data["user"]["phone"] == "+998901234567"

    # keyingi safar — telefon + parol bilan
    r = api.post(PHONE_LOGIN, {"phone": "90 123 45 67", "password": PASSWORD}, format="json")
    assert r.status_code == 200, r.data
    assert r.data["access"] and r.data["user"]["phone"] == "+998901234567"


def test_link_is_single_use_and_expires(bot, api):
    user = User.objects.create_user(email=None, phone="+998901112233", first_name="Ali")
    token = telegram_bot.issue_login_link(user)
    assert api.post(LOGIN, {"code": token}, format="json").status_code == 200
    assert api.post(LOGIN, {"code": token}, format="json").status_code == 400

    token = telegram_bot.issue_login_link(user)
    TelegramLoginLink.objects.filter(used_at__isnull=True).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert api.post(LOGIN, {"code": token}, format="json").status_code == 400
    assert api.post(LOGIN, {"code": "noto'g'ri"}, format="json").status_code == 400


def test_new_link_cancels_previous(bot, api):
    user = User.objects.create_user(email=None, phone="+998901112233", first_name="Ali")
    old = telegram_bot.issue_login_link(user)
    new = telegram_bot.issue_login_link(user)
    assert api.post(LOGIN, {"code": old}, format="json").status_code == 400
    assert api.post(LOGIN, {"code": new}, format="json").status_code == 200


def test_someone_elses_contact_rejected(bot):
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact(user_id=999)))
    assert not User.objects.exists()
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "contact"


def test_foreign_number_rejected(bot):
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact("+79161234567")))
    assert not User.objects.exists()
    assert "+998" in bot[-1]["text"]


def test_existing_user_with_password_is_linked_and_keeps_password(bot):
    user = User.objects.create_user(
        email="ali@example.com", password="x-Parol-2026", phone="+998901234567", first_name="Ali"
    )
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact()))
    user.refresh_from_db()
    assert user.telegram_id == TG_ID and user.first_name == "Ali" and User.objects.count() == 1
    assert user.check_password("x-Parol-2026")
    assert "parolingiz bilan kiring" in bot[-1]["text"] and not TelegramLoginLink.objects.exists()


def test_existing_user_without_password_skips_name_and_sets_password(bot, api):
    User.objects.create_user(email=None, phone="+998901234567", first_name="Ali")
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact()))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "password"
    telegram_bot.handle_update(msg(PASSWORD))
    telegram_bot.handle_update(msg(PASSWORD))
    user = User.objects.get()
    assert user.first_name == "Ali" and user.telegram_id == TG_ID and user.check_password(PASSWORD)
    r = api.post(LOGIN, {"code": code_from(bot)}, format="json")
    assert r.status_code == 200 and r.data["is_new"] is False


def test_registered_user_on_start_is_sent_to_site_login(bot):
    User.objects.create_user(
        email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID, password=PASSWORD
    )
    telegram_bot.handle_update(msg("/start login"))
    assert "allaqachon ro'yxatdan o'tgansiz" in bot[-1]["text"]
    assert bot[-1]["reply_markup"]["inline_keyboard"][0][0]["url"] == "https://meyzi.uz/login"
    assert not TelegramBotSession.objects.exists() and not TelegramLoginLink.objects.exists()


def test_legacy_user_without_password_asked_to_set_one(bot):
    User.objects.create_user(email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID)
    telegram_bot.handle_update(msg("/start"))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "password"


def test_password_mismatch_starts_over(bot):
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact()))
    telegram_bot.handle_update(msg("Aziz Karimov"))
    telegram_bot.handle_update(msg(PASSWORD))
    telegram_bot.handle_update(msg("Boshqa-Parol-99"))
    session = TelegramBotSession.objects.get(telegram_id=TG_ID)
    assert session.step == "password" and session.password_hash == ""
    assert "mos kelmadi" in bot[-1]["text"] and not User.objects.exists()


@pytest.mark.parametrize("weak", ["1234", "12345678901", "password", "Aziz Karimov"])
def test_weak_password_rejected(bot, weak):
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact()))
    telegram_bot.handle_update(msg("Aziz Karimov"))
    telegram_bot.handle_update(msg(weak, message_id=7))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "password"
    assert {"chat_id": TG_ID, "message_id": 7} in bot  # rad etilgan parol ham o'chiriladi
    assert "mos emas" in bot[-1]["text"]


def test_reset_password_via_bot(bot, api):
    user = User.objects.create_user(
        email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID, password="Eski-Parol-2020"
    )
    telegram_bot.handle_update(msg("/parol"))
    telegram_bot.handle_update(msg(PASSWORD))
    telegram_bot.handle_update(msg(PASSWORD))
    user.refresh_from_db()
    assert user.check_password(PASSWORD) and not user.check_password("Eski-Parol-2020")
    r = api.post(PHONE_LOGIN, {"phone": "+998901234567", "password": PASSWORD}, format="json")
    assert r.status_code == 200


def test_reset_password_from_site_link(bot):
    User.objects.create_user(
        email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID, password="Eski-Parol-2020"
    )
    telegram_bot.handle_update(msg("/start parol"))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "password"


def test_reset_password_unknown_user_starts_registration(bot):
    telegram_bot.handle_update(msg("/parol"))
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "contact"


# ---------- Saytga telefon + parol bilan kirish ----------


def test_phone_login_wrong_password_or_unknown_phone(api):
    User.objects.create_user(email=None, phone="+998901234567", first_name="Ali", password=PASSWORD)
    for phone, pw in [("+998901234567", "notogri-parol"), ("+998909999999", PASSWORD)]:
        r = api.post(PHONE_LOGIN, {"phone": phone, "password": pw}, format="json")
        assert r.status_code == 400 and r.data["detail"] == "Telefon raqam yoki parol noto'g'ri."


def test_phone_login_without_password_set(api):
    User.objects.create_user(email=None, phone="+998901234567", first_name="Ali")
    r = api.post(PHONE_LOGIN, {"phone": "+998901234567", "password": "!"}, format="json")
    assert r.status_code == 400


def test_phone_login_blocked_user(api):
    User.objects.create_user(
        email=None, phone="+998901234567", first_name="Ali", password=PASSWORD, is_active=False
    )
    r = api.post(PHONE_LOGIN, {"phone": "+998901234567", "password": PASSWORD}, format="json")
    assert r.status_code == 400 and "bloklangan" in r.data["detail"]


def test_blocked_user_cannot_log_in(bot, api):
    User.objects.create_user(
        email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID, is_active=False
    )
    telegram_bot.handle_update(msg("/start"))
    assert "bloklangan" in bot[-1]["text"]
    assert not TelegramLoginLink.objects.exists()


def test_invalid_name_asked_again(bot):
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(contact=contact()))
    telegram_bot.handle_update(msg("12345"))
    assert not User.objects.exists()
    assert TelegramBotSession.objects.get(telegram_id=TG_ID).step == "name"


def test_group_chats_ignored(bot):
    telegram_bot.handle_update(msg("/start", chat_type="group"))
    assert bot == []


def test_localhost_link_sent_as_text(bot, settings):
    settings.MEYZI_FRONTEND_URL = "http://localhost:3000"
    User.objects.create_user(email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID)
    telegram_bot.handle_update(msg("/start"))
    telegram_bot.handle_update(msg(PASSWORD))
    telegram_bot.handle_update(msg(PASSWORD))
    assert "reply_markup" not in bot[-1]
    assert "http://localhost:3000/auth/telegram?code=" in bot[-1]["text"]


def test_webhook_requires_secret(bot, api, settings):
    settings.TELEGRAM_WEBHOOK_SECRET = "s3cret"
    assert api.post(WEBHOOK, msg("/start"), format="json").status_code == 403
    r = api.post(WEBHOOK, msg("/start"), format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="s3cret")
    assert r.status_code == 200
    assert TelegramBotSession.objects.filter(telegram_id=TG_ID).exists()


def test_webhook_disabled_without_secret(bot, api):
    r = api.post(WEBHOOK, msg("/start"), format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="")
    assert r.status_code == 403


def test_features_show_telegram_login(bot, api):
    data = api.get("/api/v1/features/").json()["telegram_login"]
    assert data == {
        "enabled": True,
        "bot_username": "meyzi_test_bot",
        "url": "https://t.me/meyzi_test_bot?start=login",
    }


# ---------- Profilga email ulash (bot orqali kirganlarda email yo'q) ----------

EMAIL_REQ = "/api/v1/auth/me/email/request-code/"
EMAIL_VERIFY = "/api/v1/auth/me/email/verify/"


def last_code() -> str:
    import re

    from django.core import mail

    return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)


@pytest.fixture
def tg_user_api(db):
    from rest_framework.test import APIClient

    u = User.objects.create_user(email=None, phone="+998901234567", first_name="Ali", telegram_id=TG_ID)
    client = APIClient()
    client.force_authenticate(u)
    return u, client


def test_attach_email_with_code(tg_user_api, django_capture_on_commit_callbacks):
    from django.core import mail

    u, client = tg_user_api
    with django_capture_on_commit_callbacks(execute=True):
        r = client.post(EMAIL_REQ, {"email": "Ali@Example.com"}, format="json")
    assert r.status_code == 200, r.data
    assert mail.outbox[-1].to == ["ali@example.com"]

    assert (
        client.post(EMAIL_VERIFY, {"email": "ali@example.com", "code": "000000"}, format="json").status_code
        == 400
    )
    r = client.post(EMAIL_VERIFY, {"email": "ali@example.com", "code": last_code()}, format="json")
    assert r.status_code == 200, r.data
    u.refresh_from_db()
    assert u.email == "ali@example.com" and u.email_verified


def test_attach_email_code_bound_to_that_email(tg_user_api, django_capture_on_commit_callbacks):
    u, client = tg_user_api
    with django_capture_on_commit_callbacks(execute=True):
        client.post(EMAIL_REQ, {"email": "ali@example.com"}, format="json")
    r = client.post(EMAIL_VERIFY, {"email": "boshqa@example.com", "code": last_code()}, format="json")
    assert r.status_code == 400
    u.refresh_from_db()
    assert u.email is None


def test_attach_email_taken_by_other_user(tg_user_api):
    User.objects.create_user(email="band@example.com", password="x-Parol-2026")
    _, client = tg_user_api
    r = client.post(EMAIL_REQ, {"email": "BAND@example.com"}, format="json")
    assert r.status_code == 400 and "boshqa akkaunt" in r.data["email"]


def test_attach_email_when_already_verified(tg_user_api):
    u, client = tg_user_api
    u.email, u.email_verified = "ali@example.com", True
    u.save()
    assert client.post(EMAIL_REQ, {"email": "yangi@example.com"}, format="json").status_code == 400


def test_attach_email_requires_login(api):
    assert api.post(EMAIL_REQ, {"email": "a@example.com"}, format="json").status_code == 401
