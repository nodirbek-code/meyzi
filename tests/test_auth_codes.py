import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import OneTimeCode, User
from apps.notifications import sms, telegram_codes

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_outboxes():
    sms.outbox.clear()
    telegram_codes.outbox.clear()
    yield
    sms.outbox.clear()
    telegram_codes.outbox.clear()


@pytest.fixture
def run_on_commit(django_capture_on_commit_callbacks):
    """Kodlar on_commit'da darhol yuboriladi — testda shu callback'larni bajaramiz."""

    def _run(fn):
        with django_capture_on_commit_callbacks(execute=True):
            return fn()

    return _run


def last_email_code():
    return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)


def last_sms_code():
    """Telefon kodlari endi SMS emas — Telegram orqali (telegram_codes.outbox: (telefon, kod))."""
    return telegram_codes.outbox[-1][1]


def expire_resend_wait():
    OneTimeCode.objects.update(created_at=timezone.now() - timedelta(minutes=2))


# ---------- Ro'yxatdan o'tish + email tasdiqlash ----------


def test_register_sends_verification_and_verify(api, run_on_commit):
    res = run_on_commit(
        lambda: api.post(
            "/api/v1/auth/register/", {"email": "a@example.com", "password": PASSWORD}, format="json"
        )
    )
    assert res.status_code == 201
    assert res.data["user"]["email_verified"] is False
    assert mail.outbox[-1].to == ["a@example.com"]
    code = last_email_code()

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    assert (
        api.post(
            "/api/v1/auth/email/verify/", {"code": "000000" if code != "000000" else "111111"}
        ).status_code
        == 400
    )
    res = api.post("/api/v1/auth/email/verify/", {"code": code}, format="json")
    assert res.status_code == 200
    assert res.data["email_verified"] is True
    assert api.post("/api/v1/auth/email/send-code/").status_code == 400  # allaqachon tasdiqlangan


def test_code_is_not_stored_plain(api, run_on_commit):
    run_on_commit(
        lambda: api.post("/api/v1/auth/register/", {"email": "b@example.com", "password": PASSWORD})
    )
    code = last_email_code()
    otp = OneTimeCode.objects.get()
    assert code not in otp.code_hash and len(otp.code_hash) == 64


# ---------- Parolni tiklash ----------


def test_password_reset_flow(api, user, run_on_commit):
    login = api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json").data

    res = run_on_commit(lambda: api.post("/api/v1/auth/password/forgot/", {"email": "TURIST@example.com"}))
    assert res.status_code == 200
    code = last_email_code()

    res = api.post(
        "/api/v1/auth/password/reset/",
        {"email": user.email, "code": code, "new_password": "Yangi-Parol-2027"},
        format="json",
    )
    assert res.status_code == 204, res.data
    user.refresh_from_db()
    assert user.check_password("Yangi-Parol-2027") and user.email_verified

    # eski refresh token endi ishlamaydi (hamma qurilmalardan chiqarildi)
    assert api.post("/api/v1/auth/token/refresh/", {"refresh": login["refresh"]}).status_code == 401
    # kod ikkinchi marta ishlamaydi
    again = {"email": user.email, "code": code, "new_password": "Boshqa-Parol-2028"}
    assert api.post("/api/v1/auth/password/reset/", again, format="json").status_code == 400


def test_forgot_does_not_reveal_unknown_email(api, run_on_commit):
    res = run_on_commit(lambda: api.post("/api/v1/auth/password/forgot/", {"email": "yoq@example.com"}))
    assert res.status_code == 200
    assert mail.outbox == []


def test_five_wrong_attempts_lock_code(api, user, run_on_commit):
    run_on_commit(lambda: api.post("/api/v1/auth/password/forgot/", {"email": user.email}))
    code = last_email_code()
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        res = api.post(
            "/api/v1/auth/password/reset/",
            {"email": user.email, "code": wrong, "new_password": "Yangi-Parol-2027"},
            format="json",
        )
        assert res.status_code == 400
    assert OneTimeCode.objects.get().attempts == 5  # urinishlar so'rov xatosi bilan orqaga qaytmagan
    res = api.post(
        "/api/v1/auth/password/reset/",
        {"email": user.email, "code": code, "new_password": "Yangi-Parol-2027"},
        format="json",
    )
    assert res.status_code == 400  # to'g'ri kod ham endi qabul qilinmaydi


def test_expired_code(api, user, run_on_commit):
    run_on_commit(lambda: api.post("/api/v1/auth/password/forgot/", {"email": user.email}))
    code = last_email_code()
    OneTimeCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    data = {"email": user.email, "code": code, "new_password": "Yangi-Parol-2027"}
    assert api.post("/api/v1/auth/password/reset/", data, format="json").status_code == 400


def test_resend_throttle(api, user):
    assert api.post("/api/v1/auth/password/forgot/", {"email": user.email}).status_code == 200
    res = api.post("/api/v1/auth/password/forgot/", {"email": user.email})
    assert res.status_code == 429
    expire_resend_wait()
    assert api.post("/api/v1/auth/password/forgot/", {"email": user.email}).status_code == 200


# ---------- Telefon orqali kirish ----------


def test_phone_login_creates_user(api, run_on_commit):
    res = run_on_commit(lambda: api.post("/api/v1/auth/phone/request-code/", {"phone": "90 123 45 67"}))
    assert res.status_code == 200
    assert res.data["phone"] == "+998901234567"
    assert res.data["channel"] == "telegram"
    assert telegram_codes.outbox[-1][0] == "+998901234567"
    assert not sms.outbox  # SMS yuborilmaydi
    code = last_sms_code()

    res = api.post(
        "/api/v1/auth/phone/verify/",
        {"phone": "+998 (90) 123-45-67", "code": code, "first_name": "Ali"},
        format="json",
    )
    assert res.status_code == 200, res.data
    assert res.data["is_new"] is True
    assert res.data["user"]["phone"] == "+998901234567"
    assert res.data["user"]["email"] is None
    u = User.objects.get(phone="+998901234567")
    assert (u.first_name, u.phone_verified, u.has_usable_password()) == ("Ali", True, False)

    # ikkinchi marta — o'sha akkaunt
    expire_resend_wait()
    run_on_commit(lambda: api.post("/api/v1/auth/phone/request-code/", {"phone": "+998901234567"}))
    res = api.post(
        "/api/v1/auth/phone/verify/", {"phone": "+998901234567", "code": last_sms_code()}, format="json"
    )
    assert res.data["is_new"] is False
    assert User.objects.count() == 1

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    assert api.get("/api/v1/auth/me/").data["phone"] == "+998901234567"


@pytest.mark.parametrize("bad", ["123", "+7 900 123 45 67", "+99890123456", "abc"])
def test_invalid_phone(api, bad):
    res = api.post("/api/v1/auth/phone/request-code/", {"phone": bad})
    assert res.status_code == 400
    assert "phone" in res.data


def test_attach_phone_to_email_account(auth_api, user, run_on_commit):
    other = User.objects.create_user(email=None, phone="+998935554433")
    res = auth_api.post("/api/v1/auth/me/phone/request-code/", {"phone": "+998935554433"})
    assert res.status_code == 400  # boshqa akkauntga ulangan
    assert other.phone_verified is False

    run_on_commit(lambda: auth_api.post("/api/v1/auth/me/phone/request-code/", {"phone": "+998901112233"}))
    res = auth_api.post(
        "/api/v1/auth/me/phone/verify/", {"phone": "+998901112233", "code": last_sms_code()}, format="json"
    )
    assert res.status_code == 200
    assert (res.data["phone"], res.data["phone_verified"]) == ("+998901112233", True)


def test_me_cannot_change_phone_or_email_directly(auth_api, user):
    auth_api.patch("/api/v1/auth/me/", {"phone": "+998901112233", "email": "x@example.com"}, format="json")
    user.refresh_from_db()
    assert (user.phone, user.email) == (None, "turist@example.com")


def test_code_for_one_purpose_not_valid_for_another(api, user, run_on_commit):
    run_on_commit(lambda: api.post("/api/v1/auth/phone/request-code/", {"phone": "+998901234567"}))
    code = last_sms_code()
    data = {"email": user.email, "code": code, "new_password": "Yangi-Parol-2027"}
    assert api.post("/api/v1/auth/password/reset/", data, format="json").status_code == 400
