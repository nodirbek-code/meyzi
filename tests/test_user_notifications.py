from datetime import time, timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings import services as bookings
from apps.guides import services as guides
from apps.guides.models import GuideProfile
from apps.hotels import services as hotels
from apps.hotels.models import Hotel, HotelMember, RoomType
from apps.notifications import sms
from apps.notifications.models import UserMessage

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def msgs(**f):
    return list(UserMessage.objects.filter(**f).values_list("channel", "recipient", "event"))


@pytest.fixture(autouse=True)
def clean():
    sms.outbox.clear()


def test_tour_booking_flow_messages(user, agency, agency_user, departure):
    agency.email = "agency@example.com"
    agency.phone = "+998711234567"
    agency.save()
    user.phone, user.phone_verified = "+998901234567", True
    user.save()

    b = bookings.create_booking(
        user=user, departure_id=departure.pk, seats=2, contact_name="A", contact_phone="+998900000000"
    )
    assert msgs(event="tour_booking_created") == [("email", "turist@example.com", "tour_booking_created")]

    bookings.confirm_booking(b)
    assert set(msgs(event="tour_booking_confirmed")) == {
        ("email", "turist@example.com", "tour_booking_confirmed"),
        ("sms", "+998901234567", "tour_booking_confirmed"),
    }
    agency_side = set(msgs(event="tour_booking_confirmed_agency"))
    assert ("email", "agency@example.com", "tour_booking_confirmed_agency") in agency_side
    assert ("email", "agent@example.com", "tour_booking_confirmed_agency") in agency_side  # xodim
    assert ("sms", "+998711234567", "tour_booking_confirmed_agency") in agency_side

    bookings.cancel_booking(b, by="agency", reason="Ob-havo")
    body = UserMessage.objects.get(event="tour_booking_cancelled", channel="email").body
    assert "Ob-havo" in body and "1 780 000 so'm" in body


def test_unverified_phone_gets_no_sms(user, departure):
    user.phone, user.phone_verified = "+998901234567", False
    user.save()
    b = bookings.create_booking(
        user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="1"
    )
    bookings.confirm_booking(b)
    assert not UserMessage.objects.filter(channel="sms", recipient="+998901234567").exists()


def test_tourist_cancel_unpaid_does_not_bother_agency(user, departure):
    b = bookings.create_booking(
        user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="1"
    )
    bookings.cancel_booking(b, by="tourist")
    assert not UserMessage.objects.filter(event__startswith="tour_booking_cancelled").exists()


def test_guide_request_is_urgent_sms(user, samarqand):
    gu = User.objects.create_user(email="gid@example.com", password=PASSWORD)
    g = GuideProfile.objects.create(
        user=gu,
        slug="g",
        display_name="G",
        phone="+998935550000",
        languages=["uz"],
        price_half_day_uzs=1,
        price_full_day_uzs=100_000,
        price_per_day_uzs=1,
        status="approved",
    )
    g.destinations.add(samarqand)
    from apps.guides.models import GuideMeetingPoint

    point = GuideMeetingPoint.objects.create(
        guide=g, destination=samarqand, name="Registon", address="Samarqand", latitude=39.65, longitude=66.96
    )
    b = guides.request_booking(
        user=user,
        guide=g,
        destination=samarqand,
        duration="full_day",
        start_date=timezone.localdate() + timedelta(days=5),
        start_time=time(9),
        days=1,
        group_size=1,
        language="uz",
        meeting_point=point,
        contact_name="A",
        contact_phone="1",
    )
    assert set(msgs(event="guide_request_created")) == {
        ("email", "gid@example.com", "guide_request_created"),
        ("sms", "+998935550000", "guide_request_created"),
    }
    guides.decline(b, reason="Band")
    assert msgs(event="guide_request_declined") == [("email", "turist@example.com", "guide_request_declined")]


def test_hotel_messages(user, samarqand):
    owner = User.objects.create_user(email="owner@example.com", password=PASSWORD)
    h = Hotel.objects.create(
        name="H", slug="h", destination=samarqand, address="a", phone="+998662000000", status="approved"
    )
    HotelMember.objects.create(hotel=h, user=owner)
    rt = RoomType.objects.create(hotel=h, name="S", capacity=2, price_per_night_uzs=100_000, total_rooms=1)
    day = timezone.localdate() + timedelta(days=3)
    b = hotels.create_booking(
        user=user,
        room_type_id=rt.pk,
        check_in=day,
        check_out=day + timedelta(days=1),
        rooms=1,
        guests=1,
        contact_name="A",
        contact_phone="1",
    )
    hotels.mark_paid(b)
    assert ("email", "owner@example.com", "hotel_booking_confirmed_hotel") in msgs()
    assert ("sms", "+998662000000", "hotel_booking_confirmed_hotel") in msgs()


def test_scheduler_sends_queued(user, departure, mailoutbox):
    bookings.create_booking(
        user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="1"
    )
    call_command("send_notifications")
    assert [m.to for m in mailoutbox] == [["turist@example.com"]]
    assert UserMessage.objects.get().status == "sent"


# ---------- Telegram bot orqali bron xabari ----------


@pytest.fixture
def bot(settings, monkeypatch):
    from apps.notifications import telegram

    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.LAZURI_FRONTEND_URL = "https://lazuri.uz"
    sent = []
    monkeypatch.setattr(telegram, "call", lambda method, payload=None, **kw: sent.append((method, payload)))
    return sent


def test_booking_created_sends_bot_message_with_pay_button(
    bot, user, departure, django_capture_on_commit_callbacks
):
    user.telegram_id = 555001
    user.save(update_fields=["telegram_id"])
    with django_capture_on_commit_callbacks(execute=True):
        b = bookings.create_booking(
            user=user, departure_id=departure.pk, seats=2, contact_name="A", contact_phone="+998900000000"
        )

    msg = UserMessage.objects.get(channel="telegram", event="tour_booking_created")
    assert msg.recipient == "555001" and msg.status == UserMessage.Status.SENT
    assert len(bot) == 1
    method, payload = bot[0]
    assert method == "sendMessage" and payload["chat_id"] == "555001"
    assert b.tour.title in payload["text"]
    assert f"{timezone.localtime(b.departure_at):%d.%m.%Y %H:%M}" in payload["text"]
    button = payload["reply_markup"]["inline_keyboard"][0][0]
    assert button["url"] == f"https://lazuri.uz/account/bookings/{b.code}"
    assert "To'lov" in button["text"]


def test_booking_bot_message_localhost_link_in_text(
    bot, settings, user, departure, django_capture_on_commit_callbacks
):
    settings.LAZURI_FRONTEND_URL = "http://localhost:3000"
    user.telegram_id = 555002
    user.save(update_fields=["telegram_id"])
    with django_capture_on_commit_callbacks(execute=True):
        b = bookings.create_booking(
            user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="+998900000000"
        )
    payload = bot[0][1]
    assert "reply_markup" not in payload
    assert f"http://localhost:3000/account/bookings/{b.code}" in payload["text"]


def test_no_bot_message_without_telegram(bot, user, departure):
    bookings.create_booking(
        user=user, departure_id=departure.pk, seats=1, contact_name="A", contact_phone="+998900000000"
    )
    assert not UserMessage.objects.filter(channel="telegram").exists()
