"""
Adminlarga Telegram bildirishnomalari.

Servislar `notify_admins(...)` ni chaqiradi (yoki tayyor `booking_created(...)` kabi funksiyalarni).
Xabar bazaga yoziladi va `send_pending()` yuboradi (scheduler har 15 soniyada).
Telegram sozlanmagan bo'lsa — hech narsa yozilmaydi (keyin yoqilganda eski xabarlar to'lqini kelmaydi).
"""

import logging
from html import escape

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from . import sms, telegram
from .models import TelegramMessage, UserMessage

log = logging.getLogger(__name__)


def _money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " so'm"


def _admin_url(path: str) -> str:
    return settings.MEYZI_SITE_URL.rstrip("/") + path


def _link(text: str, path: str) -> str:
    return f'<a href="{escape(_admin_url(path))}">{escape(text)}</a>'


def _contact(booking) -> str:
    return f"👤 {escape(booking.contact_name)}, {escape(booking.contact_phone)}"


def _obj_link(text: str, obj) -> str:
    """Admin paneldagi obyekt sahifasiga havola."""
    meta = obj._meta
    return _link(text, f"/admin/{meta.app_label}/{meta.model_name}/{obj.pk}/change/")


def _booking_link(booking) -> str:
    return _link(booking.code, f"/admin/bookings/booking/{booking.pk}/change/")


def notify_admins(event: str, text: str) -> int:
    """Har bir admin chati uchun navbatga xabar qo'shadi. Nechta yozilganini qaytaradi."""
    if not telegram.is_configured():
        log.debug("Telegram sozlanmagan, xabar o'tkazib yuborildi: %s", event)
        return 0
    TelegramMessage.objects.bulk_create(
        TelegramMessage(event=event, chat_id=str(chat_id).strip(), text=text)
        for chat_id in settings.TELEGRAM_ADMIN_CHAT_IDS
        if str(chat_id).strip()
    )
    return len(settings.TELEGRAM_ADMIN_CHAT_IDS)


def send_pending(limit: int = 50) -> tuple[int, int]:
    """Navbatdagi va xato bo'lgan (urinishlar tugamagan) xabarlarni yuboradi. (yuborildi, xato) qaytaradi."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return 0, 0
    qs = TelegramMessage.objects.filter(
        Q(status=TelegramMessage.Status.PENDING)
        | Q(status=TelegramMessage.Status.FAILED, attempts__lt=TelegramMessage.MAX_ATTEMPTS)
    ).order_by("created_at")[:limit]
    sent = failed = 0
    for msg in qs:
        try:
            telegram.send_message(msg.chat_id, msg.text)
        except telegram.TelegramError as exc:
            TelegramMessage.objects.filter(pk=msg.pk).update(
                status=TelegramMessage.Status.FAILED, attempts=F("attempts") + 1, error=str(exc)[:1000]
            )
            failed += 1
        else:
            TelegramMessage.objects.filter(pk=msg.pk).update(
                status=TelegramMessage.Status.SENT,
                attempts=F("attempts") + 1,
                sent_at=timezone.now(),
                error="",
            )
            sent += 1
    return sent, failed


# ---------- Foydalanuvchilarga: email / SMS ----------


def _deliver(msg: UserMessage) -> bool:
    try:
        if msg.channel == UserMessage.Channel.EMAIL:
            send_mail(
                msg.subject, msg.body, settings.DEFAULT_FROM_EMAIL, [msg.recipient], fail_silently=False
            )
        elif msg.channel == UserMessage.Channel.TELEGRAM:
            telegram.send_message(
                msg.recipient, msg.body, button_text=msg.button_text, button_url=msg.button_url
            )
        else:
            sms.send(msg.recipient, msg.body)
    except Exception as exc:  # noqa: BLE001 — har qanday transport xatosi qayta urinishga
        UserMessage.objects.filter(pk=msg.pk).update(
            status=UserMessage.Status.FAILED, attempts=F("attempts") + 1, error=str(exc)[:1000]
        )
        return False
    UserMessage.objects.filter(pk=msg.pk).update(
        status=UserMessage.Status.SENT, attempts=F("attempts") + 1, sent_at=timezone.now(), error=""
    )
    return True


def queue_email(recipient: str, subject: str, body: str, *, event: str, immediate: bool = False):
    if not recipient:
        return None
    msg = UserMessage.objects.create(
        channel=UserMessage.Channel.EMAIL, event=event, recipient=recipient, subject=subject[:200], body=body
    )
    if immediate:
        transaction.on_commit(lambda: _deliver(msg))
    return msg


def queue_sms(phone: str, text: str, *, event: str, immediate: bool = False):
    if not phone or not sms.is_enabled():
        return None
    msg = UserMessage.objects.create(channel=UserMessage.Channel.SMS, event=event, recipient=phone, body=text)
    if immediate:
        transaction.on_commit(lambda: _deliver(msg))
    return msg


def queue_telegram(
    telegram_id: int | None,
    text: str,
    *,
    event: str,
    button_text: str = "",
    button_url: str = "",
    immediate: bool = False,
):
    """Foydalanuvchiga bot orqali xabar (u botda ro'yxatdan o'tgan bo'lsa — `user.telegram_id`)."""
    if not telegram_id or not settings.TELEGRAM_BOT_TOKEN:
        return None
    msg = UserMessage.objects.create(
        channel=UserMessage.Channel.TELEGRAM,
        event=event,
        recipient=str(telegram_id),
        body=text,
        button_text=button_text[:64],
        button_url=button_url,
    )
    if immediate:
        transaction.on_commit(lambda: _deliver(msg))
    return msg


def send_pending_user_messages(limit: int = 100) -> tuple[int, int]:
    qs = UserMessage.objects.filter(
        Q(status=UserMessage.Status.PENDING)
        | Q(status=UserMessage.Status.FAILED, attempts__lt=UserMessage.MAX_ATTEMPTS)
    ).order_by("created_at")[:limit]
    sent = failed = 0
    for msg in qs:
        if _deliver(msg):
            sent += 1
        else:
            failed += 1
    return sent, failed


# ---------- Hodisalar ----------


def booking_created(booking) -> None:
    local = timezone.localtime(booking.departure_at)
    notify_admins(
        "booking_created",
        "🆕 <b>Yangi bron</b>\n"
        f"{_booking_link(booking)} — {escape(booking.tour.title)}\n"
        f"📅 {local:%d.%m.%Y %H:%M} · 👥 {booking.seats} kishi · 💰 {_money(booking.total_uzs)}\n"
        f"🏢 {escape(booking.agency.name)}\n"
        f"👤 {escape(booking.contact_name)}, {escape(booking.contact_phone)}",
    )


def booking_cancelled(booking) -> None:
    who = booking.get_cancelled_by_display()
    refund = f"\n↩️ Qaytariladi: <b>{_money(booking.refund_uzs)}</b>" if booking.refund_uzs else ""
    reason = f"\n📝 {escape(booking.cancel_reason)}" if booking.cancel_reason else ""
    notify_admins(
        "booking_cancelled",
        f"❌ <b>Bron bekor qilindi</b> ({escape(who)})\n"
        f"{_booking_link(booking)} — {escape(booking.tour.title)}\n"
        f"👥 {booking.seats} kishi · 💰 {_money(booking.total_uzs)}{refund}{reason}",
    )


def departure_cancelled(departure, bookings_count: int, refund_total: int) -> None:
    notify_admins(
        "departure_cancelled",
        "🚫 <b>Agentlik sanani bekor qildi</b>\n"
        f"{escape(departure.tour.title)} — {departure.date:%d.%m.%Y}\n"
        f"🏢 {escape(departure.tour.agency.name)}\n"
        f"Bekor qilingan bronlar: {bookings_count} · qaytariladi: <b>{_money(refund_total)}</b>",
    )


def agency_application_created(application) -> None:
    notify_admins(
        "agency_application",
        "🏢 <b>Yangi agentlik arizasi</b>\n"
        f"{_obj_link(application.agency_name, application)}\n"
        f"👤 {escape(application.contact_person)}, {escape(application.phone)}"
        + (f"\n📝 {escape(application.message)}" if application.message else ""),
    )


def tour_submitted(tour) -> None:
    notify_admins(
        "tour_submitted",
        "🧭 <b>Tur moderatsiyaga yuborildi</b>\n"
        f"{_obj_link(tour.title, tour)}\n"
        f"🏢 {escape(tour.agency.name)} · 💰 {_money(tour.price_uzs)}",
    )


def review_created(review) -> None:
    stars = "⭐" * review.rating
    warn = "⚠️ " if review.rating <= 3 else ""
    text = escape(review.text[:300]) + ("…" if len(review.text) > 300 else "")
    notify_admins(
        "review_created",
        f"{warn}💬 <b>Yangi sharh</b> {stars}\n"
        f"{_obj_link(review.tour.title, review)}\n"
        f"🏢 {escape(review.agency.name)}\n" + (f"«{text}»" if text else ""),
    )


def changes_submitted(what: str, name: str, obj, details: str = "") -> None:
    """Tasdiqlangan hamkor ma'lumotlarini o'zgartirdi — saytdan yashirildi, qayta tekshiruv kerak."""
    notify_admins(
        "changes_submitted",
        f"✏️ <b>{escape(what)}: o'zgarishlar tekshiruvga</b>\n"
        f"{_obj_link(name, obj)}" + (f"\n📝 {escape(details)}" if details else ""),
    )


def partner_review_created(review, about: str) -> None:
    """Mehmonxona yoki gid haqida yangi sharh — admin tasdiqlagach saytga chiqadi."""
    stars = "⭐" * review.rating
    text = escape(review.text[:300]) + ("…" if len(review.text) > 300 else "")
    notify_admins(
        "review_created",
        f"💬 <b>Yangi sharh</b> {stars} (tasdiqlash kerak)\n{_obj_link(about, review)}"
        + (f"\n«{text}»" if text else ""),
    )


# ---------- Individual gidlar ----------


def guide_application(profile) -> None:
    langs = ", ".join(profile.languages)
    notify_admins(
        "guide_application",
        "🧑‍💼 <b>Gid arizasi</b> (tekshiruv kerak)\n"
        f"{_obj_link(profile.display_name, profile)}\n"
        f"📞 {escape(profile.phone)} · 🗣 {escape(langs)} · tajriba {profile.experience_years} yil",
    )


def guide_suspended(profile, reason: str) -> None:
    notify_admins(
        "guide_suspended",
        f"⛔ <b>Gid profili to'xtatildi</b>\n{_obj_link(profile.display_name, profile)}\n📝 {escape(reason)}",
    )


def guide_booking_created(booking) -> None:
    local = timezone.localtime(booking.starts_at)
    notify_admins(
        "guide_booking_created",
        "🆕 <b>Gid broni so'rovi</b>\n"
        f"{_obj_link(booking.code, booking)} — "
        f"{escape(booking.guide.display_name)}\n"
        f"📅 {local:%d.%m.%Y %H:%M} · {escape(booking.get_duration_display())}"
        f" · 👥 {booking.group_size} kishi\n"
        f"💰 {_money(booking.total_uzs)} · {_contact(booking)}",
    )


def guide_booking_cancelled(booking) -> None:
    extra = ""
    if booking.no_show == "guide":
        extra = "\n🚨 Gid kelmadi"
    if booking.guide_penalty_usd:
        extra += f"\n💸 Gidga jarima: ${booking.guide_penalty_usd}"
    refund = f"\n↩️ Qaytariladi: <b>{_money(booking.refund_uzs)}</b>" if booking.refund_uzs else ""
    notify_admins(
        "guide_booking_cancelled",
        f"❌ <b>Gid broni bekor qilindi</b> ({escape(booking.get_cancelled_by_display())})\n"
        f"{_obj_link(booking.code, booking)} — "
        f"{escape(booking.guide.display_name)}{refund}{extra}",
    )


# ---------- Mehmonxonalar ----------


def hotel_application(hotel) -> None:
    notify_admins(
        "hotel_application",
        "🏨 <b>Mehmonxona arizasi</b> (tekshiruv kerak)\n"
        f"{_obj_link(hotel.name, hotel)} — {escape(hotel.destination.name)}\n"
        f"📞 {escape(hotel.phone)}",
    )


def hotel_booking_created(booking) -> None:
    notify_admins(
        "hotel_booking_created",
        "🆕 <b>Mehmonxona broni</b>\n"
        f"{_obj_link(booking.code, booking)} — {escape(booking.hotel.name)}\n"
        f"🛏 {escape(booking.room_type.name)} × {booking.rooms} · "
        f"{booking.check_in:%d.%m} → {booking.check_out:%d.%m} ({booking.nights} kecha)\n"
        f"💰 {_money(booking.total_uzs)} · {_contact(booking)}",
    )


def hotel_booking_cancelled(booking) -> None:
    refund = f"\n↩️ Qaytariladi: <b>{_money(booking.refund_uzs)}</b>" if booking.refund_uzs else ""
    notify_admins(
        "hotel_booking_cancelled",
        f"❌ <b>Mehmonxona broni bekor qilindi</b> ({escape(booking.get_cancelled_by_display())})\n"
        f"{_obj_link(booking.code, booking)} — {escape(booking.hotel.name)}"
        f"{refund}",
    )
