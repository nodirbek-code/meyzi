import pytest
from django.core.management import call_command

from apps.bookings import services as booking_services
from apps.bookings.models import Booking
from apps.notifications import services, telegram
from apps.notifications.models import TelegramMessage

from .conftest import phone_token

pytestmark = pytest.mark.django_db


@pytest.fixture
def tg(settings, monkeypatch):
    """Telegram yoqilgan, lekin tarmoqqa chiqmaydi — yuborilganlar ro'yxatga yoziladi."""
    settings.TELEGRAM_BOT_TOKEN = "123:TEST"
    settings.TELEGRAM_ADMIN_CHAT_IDS = ["111", "222"]
    sent = []
    monkeypatch.setattr(telegram, "send_message", lambda chat_id, text: sent.append((chat_id, text)))
    return sent


def make_booking(user, departure, **extra):
    return booking_services.create_booking(
        user=user,
        departure_id=departure.pk,
        seats=2,
        contact_name=extra.get("contact_name", "Ali"),
        contact_phone="+998901234567",
    )


def test_disabled_by_default(user, departure):
    make_booking(user, departure)
    assert TelegramMessage.objects.count() == 0


def test_booking_created_queued_for_each_admin(tg, user, departure):
    booking = make_booking(user, departure)
    msgs = TelegramMessage.objects.filter(event="booking_created")
    assert sorted(m.chat_id for m in msgs) == ["111", "222"]
    assert booking.code in msgs[0].text
    assert "1 780 000 so'm" in msgs[0].text
    assert tg == []  # so'rov paytida yuborilmaydi — faqat navbat


def test_send_pending_marks_sent(tg, user, departure):
    make_booking(user, departure)
    call_command("send_notifications")
    assert len(tg) == 2
    assert set(TelegramMessage.objects.values_list("status", flat=True)) == {"sent"}
    call_command("send_notifications")
    assert len(tg) == 2  # qayta yuborilmaydi


def test_failure_retried_then_gives_up(tg, settings, monkeypatch, user, departure):
    settings.TELEGRAM_ADMIN_CHAT_IDS = ["111"]
    make_booking(user, departure)

    def boom(chat_id, text):
        raise telegram.TelegramError("Tarmoq xatosi")

    monkeypatch.setattr(telegram, "send_message", boom)
    for _ in range(TelegramMessage.MAX_ATTEMPTS + 2):
        services.send_pending()
    msg = TelegramMessage.objects.get()
    assert (msg.status, msg.attempts, msg.error) == ("failed", TelegramMessage.MAX_ATTEMPTS, "Tarmoq xatosi")


def test_user_input_is_html_escaped(tg, user, departure):
    make_booking(user, departure, contact_name="<b>Hacker</b> & co")
    text = TelegramMessage.objects.filter(chat_id="111").get().text
    assert "&lt;b&gt;Hacker&lt;/b&gt; &amp; co" in text


def test_cancel_notifies(tg, user, departure):
    booking = make_booking(user, departure)
    booking_services.cancel_booking(booking, by=Booking.CancelledBy.TOURIST, reason="Reja o'zgardi")
    assert TelegramMessage.objects.filter(event="booking_cancelled").count() == 2


def test_departure_cancel_sends_one_summary(tg, settings, user, departure):
    from apps.accounts.models import User

    settings.TELEGRAM_ADMIN_CHAT_IDS = ["111"]
    make_booking(user, departure)
    make_booking(User.objects.create_user(email="z@example.com", password="Kuchli-Parol-2026"), departure)
    booking_services.cancel_departure(departure)
    assert TelegramMessage.objects.filter(event="booking_cancelled").count() == 0
    summary = TelegramMessage.objects.get(event="departure_cancelled")
    assert "Bekor qilingan bronlar: 2" in summary.text


def test_agency_application_notifies(tg, api):
    api.post(
        "/api/v1/agencies/applications/",
        {
            "agency_name": "Yangi Tur",
            "contact_person": "Aziz",
            "phone": "+998900000000",
            "phone_token": phone_token("+998900000000"),
        },
        format="json",
    )
    assert TelegramMessage.objects.filter(event="agency_application").count() == 2


def test_tour_submit_notifies(tg, agency_api, tour, settings, tmp_path):
    from apps.tours.models import Tour, TourMedia

    settings.MEDIA_ROOT = tmp_path
    Tour.objects.filter(pk=tour.pk).update(status=Tour.Status.DRAFT)
    TourMedia.objects.create(tour=tour, file="tours/x.png", is_cover=True)
    res = agency_api.post(f"/api/v1/cabinet/tours/{tour.slug}/submit/")
    assert res.data["status"] == "pending_review"
    assert TelegramMessage.objects.filter(event="tour_submitted").count() == 2
