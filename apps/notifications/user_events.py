"""
Foydalanuvchilarga (turist, agentlik, gid, mehmonxona) email va SMS bildirishnomalari.

Qoida: muhim/shoshilinch xabar — email + SMS (telefon tasdiqlangan bo'lsa yoki tashkilot telefoni);
qolganlari — faqat email. Xabarlar navbatga yoziladi, scheduler yuboradi.
Matnlar hozircha o'zbekcha (ko'p tilli kontent — "Tez kunda").
Turistga boradigan xabarlarda bron kodi (LZ…/LG…/LH…) ko'rsatilmaydi — faqat hamkor va admin uchun.
"""

from html import escape

from django.conf import settings
from django.utils import timezone

from .services import queue_email, queue_sms, queue_telegram

SIGN = f"\n\n— {settings.BRAND_NAME}"


def _money(v: int) -> str:
    return f"{v:,}".replace(",", " ") + " so'm"


def _dt(value) -> str:
    return f"{timezone.localtime(value):%d.%m.%Y %H:%M}"


def _to_user(user, subject: str, body: str, *, event: str, sms_text: str = "") -> None:
    if user.email:
        queue_email(user.email, subject, body + SIGN, event=event)
    if sms_text and user.phone and user.phone_verified:
        queue_sms(user.phone, f"{settings.BRAND_NAME}: {sms_text}", event=event)


def _to_org(*, emails, phone: str, subject: str, body: str, event: str, sms_text: str = "") -> None:
    for email in {e for e in emails if e}:
        queue_email(email, subject, body + SIGN, event=event)
    if sms_text and phone:
        queue_sms(phone, f"{settings.BRAND_NAME}: {sms_text}", event=event)


def _tg(users, text: str, *, event: str, button_text: str = "", path: str = "") -> None:
    """Telegram bot orqali (botga ulangan foydalanuvchilarga)."""
    url = f"{settings.MEYZI_FRONTEND_URL}{path}" if path else ""
    for tg_id in {u.telegram_id for u in users if u and u.telegram_id}:
        queue_telegram(tg_id, text, event=event, button_text=button_text, button_url=url)


def _members(org):
    return [m.user for m in org.members.select_related("user")]


def _moderation_text(name: str, approved: bool, note: str, what: str) -> str:
    if approved:
        return f"✅ {what} «{name}» tasdiqlandi va saytda ko'rinmoqda."
    return (
        f"↩️ {what} «{name}» qaytarildi — tuzatish kerak.\n\n"
        f"Admin izohi:\n{note or '—'}\n\n"
        "Kabinetda tuzating — o'zgarishlar qayta tekshiruvga yuboriladi."
    )


def _agency_emails(agency):
    return [agency.email, *(m.user.email for m in agency.members.select_related("user"))]


def _hotel_emails(hotel):
    return [hotel.email, *(m.user.email for m in hotel.members.select_related("user"))]


# ---------- Tur bronlari ----------


def tour_booking_created(b) -> None:
    _to_user(
        b.user,
        f"Bron yaratildi — {b.tour.title}",
        f"Bron yaratildi: {b.tour.title}\n"
        f"Sana: {_dt(b.departure_at)}, {b.seats} kishi, jami {_money(b.total_uzs)}.\n"
        f"Joylaringiz {_dt(b.expires_at)} gacha band qilindi.",
        event="tour_booking_created",
    )
    # Bot orqali — darhol, to'lov sahifasiga tugma bilan (faqat Telegram'i ulangan foydalanuvchiga)
    queue_telegram(
        b.user.telegram_id,
        "🧾 <b>Bron yaratildi</b>\n\n"
        f"🧭 Tur: <b>{escape(b.tour.title)}</b>\n"
        f"📅 Sana: {_dt(b.departure_at)}\n"
        f"👥 {b.seats} kishi · 💰 {_money(b.total_uzs)}\n\n"
        f"⏳ Joylaringiz <b>{_dt(b.expires_at)}</b> gacha band qilindi — shu vaqtgacha to'lov qiling, "
        "aks holda bron bekor bo'ladi.",
        event="tour_booking_created",
        button_text="💳 To'lov qilish",
        button_url=f"{settings.MEYZI_FRONTEND_URL}/account/bookings/{b.code}",
        immediate=True,
    )


def tour_booking_confirmed(b) -> None:
    meeting = f"\nUchrashuv joyi: {b.tour.meeting_point}" if b.tour.meeting_point else ""
    _to_user(
        b.user,
        f"Bron tasdiqlandi — {b.tour.title}",
        f"Broningiz tasdiqlandi.\n{b.tour.title}\nJo'nash: {_dt(b.departure_at)}, {b.seats} kishi."
        f"{meeting}\nTashkilotchi: {b.agency.name}, {b.agency.phone}",
        event="tour_booking_confirmed",
        sms_text=f"broningiz tasdiqlandi. {b.tour.title}, {_dt(b.departure_at)}.",
    )
    _to_org(
        emails=_agency_emails(b.agency),
        phone=b.agency.phone,
        subject=f"Yangi bron {b.code} — {b.tour.title}",
        body=f"Yangi to'langan bron: {b.tour.title}, {_dt(b.departure_at)}\n"
        f"{b.seats} kishi, {b.contact_name}, {b.contact_phone}\n"
        f"Sizga: {_money(b.agency_amount_uzs)}",
        event="tour_booking_confirmed_agency",
        sms_text=f"yangi bron {b.code}: {b.tour.title}, {_dt(b.departure_at)}, {b.seats} kishi.",
    )


def tour_booking_cancelled(b) -> None:
    refund = f"\nQaytariladigan summa: {_money(b.refund_uzs)}." if b.refund_uzs else ""
    if b.cancelled_by != "tourist":
        _to_user(
            b.user,
            f"Bron bekor qilindi — {b.tour.title}",
            f"Afsuski, «{b.tour.title}» broningiz tashkilotchi tomonidan bekor qilindi.\n"
            f"Sabab: {b.cancel_reason or '—'}{refund}",
            event="tour_booking_cancelled",
            sms_text=f"«{b.tour.title}» broningiz bekor qilindi.{' Pul qaytariladi.' if b.refund_uzs else ''}",
        )
    elif b.confirmed_at:  # to'langan bronni turist bekor qildi — agentlikka xabar
        _to_org(
            emails=_agency_emails(b.agency),
            phone="",
            subject=f"Bron bekor qilindi {b.code}",
            body=f"Turist {b.code} bronini bekor qildi: {b.tour.title}, {_dt(b.departure_at)}, {b.seats} kishi.",
            event="tour_booking_cancelled_agency",
        )


# ---------- Agentlik va turlar ----------


def agency_application_reviewed(application) -> None:
    approved = application.status == "approved"
    subject = (
        f"{settings.BRAND_NAME}: arizangiz tasdiqlandi"
        if approved
        else f"{settings.BRAND_NAME}: arizangiz bo'yicha javob"
    )
    body = (
        f"«{application.agency_name}» agentligi platformaga qo'shildi. Kabinetga kirib, turlaringizni qo'shing."
        if approved
        else f"Afsuski, «{application.agency_name}» arizasi rad etildi.\nIzoh: {application.admin_note or '—'}"
    )
    emails = [application.email, application.user.email if application.user else None]
    _to_org(
        emails=emails,
        phone=application.phone,
        subject=subject,
        body=body,
        event="agency_application_reviewed",
    )


def tour_moderated(tour) -> None:
    approved = tour.status == "published"
    text = _moderation_text(tour.title, approved, tour.moderation_note, "Tur")
    _to_org(
        emails=_agency_emails(tour.agency),
        phone="",
        subject=f"Tur {'e’lon qilindi' if approved else 'qaytarildi'}: {tour.title}",
        body=text,
        event="tour_moderated",
    )
    _tg(_members(tour.agency), text, event="tour_moderated", button_text="Kabinet", path="/cabinet/agency")


def agency_moderated(agency) -> None:
    approved = agency.moderation_status == "approved"
    text = _moderation_text(agency.name, approved, agency.moderation_note, "Agentlik profili")
    _to_org(
        emails=_agency_emails(agency),
        phone="",
        subject=f"{settings.BRAND_NAME}: agentlik profili",
        body=text,
        event=f"agency_moderation_{agency.moderation_status}",
    )
    _tg(_members(agency), text, event="agency_moderated", button_text="Kabinet", path="/cabinet/agency")


# ---------- Individual gidlar ----------


def guide_request_created(b) -> None:
    guide = b.guide
    _to_org(
        emails=[guide.user.email],
        phone=guide.phone,
        subject=f"Yangi so'rov {b.code}",
        body=f"Yangi bron so'rovi: {b.get_duration_display()}, {_dt(b.starts_at)}, {b.group_size} kishi, "
        f"til: {b.language}.\nSizga: {_money(b.guide_amount_uzs)}\n"
        f"Javob berish muddati: {_dt(b.respond_by)}. Kabinetda qabul qiling yoki rad eting.",
        event="guide_request_created",
        sms_text=f"yangi so'rov {b.code}, {_dt(b.starts_at)}. {_dt(b.respond_by)} gacha javob bering.",
    )


def guide_request_answered(b) -> None:
    texts = {
        "accepted": (
            "Gid so'rovingizni qabul qildi",
            f"{b.guide.display_name} so'rovingizni qabul qildi. To'lovdan keyin bron tasdiqlanadi.",
        ),
        "declined": (
            "Gid so'rovni rad etdi",
            f"{b.guide.display_name} so'rovingizni rad etdi. Sabab: {b.decline_reason or '—'}. Boshqa gidni tanlang.",
        ),
        "expired": (
            "Gid javob bermadi",
            f"{b.guide.display_name} belgilangan muddatda javob bermadi. Boshqa gidni tanlang.",
        ),
    }
    subject, body = texts[b.status]
    _to_user(b.user, f"{subject} — {b.guide.display_name}", body, event=f"guide_request_{b.status}")


def guide_booking_confirmed(b) -> None:
    _to_user(
        b.user,
        f"Gid broni tasdiqlandi — {b.guide.display_name}",
        f"Gid: {b.guide.display_name}, {b.guide.phone}\nBoshlanish: {_dt(b.starts_at)}\nUchrashuv: {b.meeting_point}",
        event="guide_booking_confirmed",
        sms_text=f"gid broni tasdiqlandi. {b.guide.display_name}, {b.guide.phone}.",
    )
    _to_org(
        emails=[b.guide.user.email],
        phone=b.guide.phone,
        subject=f"Bron to'landi — {b.code}",
        body=f"{b.code} to'landi. {_dt(b.starts_at)}, {b.meeting_point}\nTurist: {b.contact_name}, {b.contact_phone}",
        event="guide_booking_confirmed_guide",
        sms_text=f"{b.code} to'landi. {_dt(b.starts_at)}, turist {b.contact_phone}.",
    )


def guide_booking_cancelled(b) -> None:
    refund = f"\nQaytariladigan summa: {_money(b.refund_uzs)}." if b.refund_uzs else ""
    if b.cancelled_by == "tourist":
        _to_org(
            emails=[b.guide.user.email],
            phone=b.guide.phone if b.confirmed_at else "",
            subject=f"Bron bekor qilindi — {b.code}",
            body=f"Turist {b.code} ({_dt(b.starts_at)}) bronini bekor qildi.",
            event="guide_booking_cancelled_guide",
            sms_text=f"{b.code} turist tomonidan bekor qilindi.",
        )
    else:
        _to_user(
            b.user,
            f"Gid broni bekor qilindi — {b.guide.display_name}",
            f"{b.guide.display_name} bilan {_dt(b.starts_at)} dagi broningiz bekor qilindi.\nSabab: {b.cancel_reason or '—'}{refund}",
            event="guide_booking_cancelled",
            sms_text=f"gid broni ({_dt(b.starts_at)}) bekor qilindi.{' Pul qaytariladi.' if b.refund_uzs else ''}",
        )


def guide_profile_status(profile) -> None:
    texts = {
        "approved": _moderation_text(profile.display_name, True, "", "Gid profili"),
        "rejected": _moderation_text(profile.display_name, False, profile.moderation_note, "Gid profili"),
        "suspended": f"Gid profilingiz vaqtincha to'xtatildi. Sabab: {profile.moderation_note or '—'}.",
    }
    if profile.status in texts:
        _to_user(
            profile.user,
            f"{settings.BRAND_NAME}: gid profili",
            texts[profile.status],
            event=f"guide_profile_{profile.status}",
        )
        _tg(
            [profile.user],
            texts[profile.status],
            event="guide_profile",
            button_text="Kabinet",
            path="/cabinet/guide",
        )


# ---------- Mehmonxonalar ----------


def hotel_booking_confirmed(b) -> None:
    hotel = b.hotel
    _to_user(
        b.user,
        f"Mehmonxona broni tasdiqlandi — {hotel.name}",
        f"{hotel.name}, {hotel.address}\n{b.room_type.name} × {b.rooms}\n"
        f"Kirish: {b.check_in:%d.%m.%Y} {hotel.check_in_time:%H:%M} dan, chiqish: {b.check_out:%d.%m.%Y} "
        f"{hotel.check_out_time:%H:%M} gacha.\nTelefon: {hotel.phone}",
        event="hotel_booking_confirmed",
        sms_text=f"mehmonxona broni tasdiqlandi. {hotel.name}, {b.check_in:%d.%m}.",
    )
    _to_org(
        emails=_hotel_emails(hotel),
        phone=hotel.phone,
        subject=f"Yangi bron {b.code}",
        body=f"{b.room_type.name} × {b.rooms}, {b.check_in:%d.%m.%Y} → {b.check_out:%d.%m.%Y} ({b.nights} kecha), "
        f"{b.guests} mehmon.\nMehmon: {b.contact_name}, {b.contact_phone}\nSizga: {_money(b.hotel_amount_uzs)}",
        event="hotel_booking_confirmed_hotel",
        sms_text=f"yangi bron {b.code}, {b.check_in:%d.%m}–{b.check_out:%d.%m}.",
    )


def hotel_booking_cancelled(b) -> None:
    refund = f"\nQaytariladigan summa: {_money(b.refund_uzs)}." if b.refund_uzs else ""
    if b.cancelled_by == "tourist":
        if b.confirmed_at:
            _to_org(
                emails=_hotel_emails(b.hotel),
                phone="",
                subject=f"Bron bekor qilindi {b.code}",
                body=f"Mehmon {b.code} ({b.check_in:%d.%m.%Y}) bronini bekor qildi.",
                event="hotel_booking_cancelled_hotel",
            )
    else:
        _to_user(
            b.user,
            f"Mehmonxona broni bekor qilindi — {b.hotel.name}",
            f"{b.hotel.name}: {b.check_in:%d.%m.%Y} dagi broningiz bekor qilindi.\nSabab: {b.cancel_reason or '—'}{refund}",
            event="hotel_booking_cancelled",
            sms_text=f"mehmonxona broni ({b.hotel.name}, {b.check_in:%d.%m}) bekor qilindi.",
        )


def hotel_status(hotel) -> None:
    texts = {
        "approved": _moderation_text(hotel.name, True, "", "Mehmonxona"),
        "rejected": _moderation_text(hotel.name, False, hotel.moderation_note, "Mehmonxona"),
        "suspended": f"«{hotel.name}» vaqtincha to'xtatildi. {settings.BRAND_NAME} bilan bog'laning.",
    }
    if hotel.status in texts:
        _to_org(
            emails=_hotel_emails(hotel),
            phone="",
            subject=f"{settings.BRAND_NAME}: mehmonxona holati",
            body=texts[hotel.status],
            event=f"hotel_{hotel.status}",
        )
        _tg(
            _members(hotel),
            texts[hotel.status],
            event="hotel_status",
            button_text="Kabinet",
            path="/cabinet/hotel",
        )
