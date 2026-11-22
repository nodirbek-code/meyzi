"""Individual gidlar — biznes mantiq. Qoidalar: policies.py."""

from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, F
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.notifications import services as notify
from apps.notifications import user_events

from . import policies
from .models import GuideBooking, GuideProfile, GuideReview, GuideUnavailableDate

D = GuideBooking.Duration


def _money(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), ROUND_HALF_UP))


# ---------- Profil ----------


def unique_guide_slug(name: str) -> str:
    base = slugify(name) or "gid"
    slug, n = base, 2
    while GuideProfile.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def clear_precheck(obj) -> list[str]:
    """Moderator tekshiruvini bekor qiladi (hamkor o'zgartirdi yoki admin qaytardi) — qayta boshidan."""
    obj.prechecked_by = None
    obj.prechecked_at = None
    obj.precheck_note = ""
    return ["prechecked_by", "prechecked_at", "precheck_note"]


@transaction.atomic
def submit_profile(profile: GuideProfile, *, is_new: bool, details: str = "") -> GuideProfile:
    """Yangi profil yoki tahrir (tasdiqlangan/qaytarilgan) — tekshiruvga; tekshiruvda saytdan yashirin."""
    was = profile.status
    if was == GuideProfile.Status.PENDING and profile.prechecked_at and not is_new:
        # moderator tekshirib bo'lgan edi — gid yana o'zgartirdi: qayta moderatorga
        profile.save(update_fields=["updated_at", *clear_precheck(profile)])
    if is_new or was in (GuideProfile.Status.REJECTED, GuideProfile.Status.APPROVED):
        profile.status = GuideProfile.Status.PENDING
        profile.save(update_fields=["status", "updated_at", *clear_precheck(profile)])
        if profile.user.role == User.Role.TOURIST:
            profile.user.role = User.Role.GUIDE
            profile.user.save(update_fields=["role"])
        if is_new:
            notify.guide_application(profile)
        else:
            notify.changes_submitted("Gid", profile.display_name, profile, details)
    return profile


def reject_profile(profile: GuideProfile, note: str) -> GuideProfile:
    """Admin qaytaradi: izoh gidga yuboriladi, u tuzatib qayta yuboradi."""
    profile.status = GuideProfile.Status.REJECTED
    profile.moderation_note = note
    profile.save(update_fields=["status", "moderation_note", "updated_at", *clear_precheck(profile)])
    user_events.guide_profile_status(profile)
    return profile


def set_review_published(review: GuideReview, published: bool) -> GuideReview:
    review.is_published = published
    review.is_moderated = True
    review.save(update_fields=["is_published", "is_moderated"])
    recalculate_rating(review.guide_id)
    return review


def approve_profile(profile: GuideProfile) -> GuideProfile:
    profile.status = GuideProfile.Status.APPROVED
    profile.approved_at = profile.approved_at or timezone.now()
    profile.moderation_note = ""
    profile.save()
    user_events.guide_profile_status(profile)
    return profile


def suspend_profile(profile: GuideProfile, reason: str) -> GuideProfile:
    profile.status = GuideProfile.Status.SUSPENDED
    profile.moderation_note = reason
    profile.save(update_fields=["status", "moderation_note", "updated_at"])
    notify.guide_suspended(profile, reason)
    user_events.guide_profile_status(profile)
    return profile


# ---------- Narx ----------


def quote(guide: GuideProfile, *, duration: str, days: int, group_size: int) -> dict:
    if duration == D.HALF_DAY:
        unit, days = guide.price_half_day_uzs, 1
    elif duration == D.FULL_DAY:
        unit, days = guide.price_full_day_uzs, 1
    else:
        unit = guide.price_per_day_uzs
    base = unit * days
    surcharge = 0
    if group_size >= settings.MEYZI_GUIDE_GROUP_THRESHOLD:
        surcharge = _money(Decimal(base) * guide.group_surcharge_percent / 100)
    total = base + surcharge
    commission = _money(Decimal(total) * guide.commission_percent / 100)
    return {
        "duration": duration,
        "days": days,
        "group_size": group_size,
        "unit_price_uzs": unit,
        "base_uzs": base,
        "surcharge_uzs": surcharge,
        "total_uzs": total,
        "commission_percent": guide.commission_percent,
        "commission_uzs": commission,
        "guide_amount_uzs": total - commission,
    }


# ---------- Bandlik ----------


def busy_dates(guide: GuideProfile, *, start: date, end: date, exclude_booking_id=None) -> set[date]:
    """Gid band kunlari: o'zi belgilagan + faol bronlar."""
    result = set(
        GuideUnavailableDate.objects.filter(guide=guide, date__range=(start, end)).values_list(
            "date", flat=True
        )
    )
    bookings = GuideBooking.objects.filter(
        guide=guide,
        status__in=GuideBooking.ACTIVE_STATUSES,
        start_date__lte=end,
        start_date__gte=start - timedelta(days=60),
    )
    if exclude_booking_id:
        bookings = bookings.exclude(pk=exclude_booking_id)
    for b in bookings.only("start_date", "days"):
        for i in range(b.days):
            d = b.start_date + timedelta(days=i)
            if start <= d <= end:
                result.add(d)
    return result


# ---------- Bron ----------


@transaction.atomic
def request_booking(
    *,
    user,
    guide: GuideProfile,
    destination,
    duration: str,
    start_date: date,
    start_time: time,
    days: int,
    group_size: int,
    language: str,
    meeting_point,
    contact_name: str,
    contact_phone: str,
    note: str = "",
    now: datetime | None = None,
) -> GuideBooking:
    now = now or timezone.now()
    guide = GuideProfile.objects.select_for_update().get(pk=guide.pk)  # bir kunga ikki bron tushmasin

    if not guide.is_approved:
        raise ValidationError({"guide": "Bu gid hozir bron qabul qilmaydi."})
    if guide.user_id == user.pk:
        raise ValidationError({"guide": "O'zingizni bron qila olmaysiz."})
    if not guide.destinations.filter(pk=destination.pk).exists():
        raise ValidationError({"destination": "Gid bu shaharda ishlamaydi."})
    # Uchrashuv joyi — faqat gid belgilagan ro'yxatdan (turist o'zi xohlagan joyni yoza olmaydi)
    if (
        meeting_point is None
        or getattr(meeting_point, "guide_id", None) != guide.pk
        or not meeting_point.is_active
    ):
        raise ValidationError({"meeting_point": "Gid belgilagan uchrashuv joylaridan birini tanlang."})
    if meeting_point.destination_id != destination.pk:
        raise ValidationError({"meeting_point": "Bu uchrashuv joyi tanlangan shaharda emas."})
    if language not in guide.languages:
        raise ValidationError({"language": "Gid bu tilda gapirmaydi."})
    if group_size < 1 or group_size > guide.max_group_size:
        raise ValidationError(
            {"group_size": f"Guruh 1 dan {guide.max_group_size} kishigacha bo'lishi mumkin."}
        )
    if duration == D.MULTI_DAY:
        if days < 2 or days > 14:
            raise ValidationError({"days": "Ko'p kunlik bron 2 dan 14 kungacha."})
    else:
        days = 1

    starts_at = timezone.make_aware(datetime.combine(start_date, start_time))
    if starts_at < now + timedelta(hours=settings.MEYZI_GUIDE_RESPONSE_HOURS):
        hours = settings.MEYZI_GUIDE_RESPONSE_HOURS
        raise ValidationError(
            {"start_date": f"Gid javob berishi uchun kamida {hours} soat oldin bron qiling."}
        )

    end_date = start_date + timedelta(days=days - 1)
    if busy_dates(guide, start=start_date, end=end_date):
        raise ValidationError({"start_date": "Gid bu kun(lar)da band."})

    pending = GuideBooking.objects.filter(user=user, status=GuideBooking.Status.REQUESTED).count()
    if pending >= settings.MEYZI_MAX_PENDING_BOOKINGS:
        raise ValidationError({"detail": "Javob kutilayotgan so'rovlaringiz juda ko'p."})

    q = quote(guide, duration=duration, days=days, group_size=group_size)
    booking = GuideBooking.objects.create(
        user=user,
        guide=guide,
        destination=destination,
        duration=duration,
        start_date=start_date,
        days=q["days"],
        start_time=start_time,
        starts_at=starts_at,
        group_size=group_size,
        language=language,
        unit_price_uzs=q["unit_price_uzs"],
        base_uzs=q["base_uzs"],
        surcharge_uzs=q["surcharge_uzs"],
        total_uzs=q["total_uzs"],
        commission_percent=q["commission_percent"],
        commission_uzs=q["commission_uzs"],
        guide_amount_uzs=q["guide_amount_uzs"],
        meeting_place=meeting_point,
        meeting_point=meeting_point.as_text,
        meeting_latitude=meeting_point.latitude,
        meeting_longitude=meeting_point.longitude,
        note=note,
        contact_name=contact_name,
        contact_phone=contact_phone,
        respond_by=min(now + timedelta(hours=settings.MEYZI_GUIDE_RESPONSE_HOURS), starts_at),
    )
    notify.guide_booking_created(booking)
    user_events.guide_request_created(booking)
    return booking


def _locked(booking: GuideBooking) -> GuideBooking:
    return GuideBooking.objects.select_for_update().select_related("guide").get(pk=booking.pk)


@transaction.atomic
def accept(booking: GuideBooking, *, now: datetime | None = None) -> GuideBooking:
    now = now or timezone.now()
    booking = _locked(booking)
    if booking.status != GuideBooking.Status.REQUESTED:
        raise ValidationError({"detail": f"Qabul qilib bo'lmaydi: holati — {booking.get_status_display()}."})
    if booking.respond_by and booking.respond_by <= now:
        raise ValidationError({"detail": "Javob berish muddati o'tgan."})
    booking.status = GuideBooking.Status.ACCEPTED
    booking.accepted_at = now
    booking.save(update_fields=["status", "accepted_at", "updated_at"])
    user_events.guide_request_answered(booking)
    return booking


@transaction.atomic
def decline(booking: GuideBooking, *, reason: str) -> GuideBooking:
    booking = _locked(booking)
    if booking.status != GuideBooking.Status.REQUESTED:
        raise ValidationError(
            {"detail": "Faqat javob kutilayotgan so'rovni rad etish mumkin. Aks holda — bekor qiling."}
        )
    booking.status = GuideBooking.Status.DECLINED
    booking.decline_reason = reason
    booking.save(update_fields=["status", "decline_reason", "updated_at"])
    user_events.guide_request_answered(booking)
    return booking


@transaction.atomic
def mark_paid(booking: GuideBooking, *, now: datetime | None = None) -> GuideBooking:
    """To'lov o'tdi (hozircha admin belgilaydi; to'lov tizimi ulanganda — webhook)."""
    now = now or timezone.now()
    booking = _locked(booking)
    if booking.status == GuideBooking.Status.CONFIRMED:
        return booking
    if booking.status != GuideBooking.Status.ACCEPTED:
        raise ValidationError({"detail": "Faqat gid qabul qilgan bronni to'langan deb belgilash mumkin."})
    booking.status = GuideBooking.Status.CONFIRMED
    booking.confirmed_at = now
    booking.save(update_fields=["status", "confirmed_at", "updated_at"])
    user_events.guide_booking_confirmed(booking)
    return booking


def refund_preview(booking: GuideBooking, *, by: str, now: datetime | None = None) -> int:
    now = now or timezone.now()
    if booking.status != GuideBooking.Status.CONFIRMED:
        return 0  # to'lanmagan
    if by in (GuideBooking.CancelledBy.GUIDE, GuideBooking.CancelledBy.ADMIN):
        return booking.total_uzs
    return _money(Decimal(booking.total_uzs) * policies.tourist_refund_ratio(booking.starts_at - now))


@transaction.atomic
def cancel(booking: GuideBooking, *, by: str, reason: str = "", now: datetime | None = None) -> GuideBooking:
    now = now or timezone.now()
    booking = _locked(booking)
    if booking.status not in GuideBooking.ACTIVE_STATUSES:
        raise ValidationError({"detail": f"Bekor qilib bo'lmaydi: holati — {booking.get_status_display()}."})
    if by != GuideBooking.CancelledBy.ADMIN and booking.starts_at <= now:
        raise ValidationError({"detail": "Xizmat boshlangan — bekor qilib bo'lmaydi."})
    if by == GuideBooking.CancelledBy.GUIDE and booking.status == GuideBooking.Status.REQUESTED:
        raise ValidationError({"detail": "Javob kutilayotgan so'rovni bekor qilmang — rad eting."})

    booking.refund_uzs = refund_preview(booking, by=by, now=now)
    if by == GuideBooking.CancelledBy.GUIDE:
        penalty, warnings = policies.guide_cancel_penalty(booking.starts_at - now)
        booking.guide_penalty_usd = penalty
        booking.guide_warnings = warnings
        if warnings:
            GuideProfile.objects.filter(pk=booking.guide_id).update(
                warnings_count=F("warnings_count") + warnings
            )
    booking.status = GuideBooking.Status.CANCELLED
    booking.cancelled_at = now
    booking.cancelled_by = by
    booking.cancel_reason = reason
    booking.save()
    notify.guide_booking_cancelled(booking)
    user_events.guide_booking_cancelled(booking)
    return booking


@transaction.atomic
def report_tourist_no_show(booking: GuideBooking, *, now: datetime | None = None) -> GuideBooking:
    """Gid belgilaydi: turist kelmadi (boshlanishdan 1 soat o'tgach). Qaytarilmaydi, gidga 30%."""
    now = now or timezone.now()
    booking = _locked(booking)
    if booking.status != GuideBooking.Status.CONFIRMED:
        raise ValidationError({"detail": "Faqat tasdiqlangan bron uchun."})
    if now < booking.starts_at + policies.TOURIST_NO_SHOW_WAIT:
        raise ValidationError({"detail": "Turistni boshlanish vaqtidan keyin kamida 1 soat kuting."})
    share = _money(Decimal(booking.total_uzs) * policies.TOURIST_NO_SHOW_GUIDE_SHARE)
    booking.status = GuideBooking.Status.COMPLETED
    booking.no_show = GuideBooking.NoShow.TOURIST
    booking.refund_uzs = 0
    booking.guide_amount_uzs = share
    booking.commission_uzs = booking.total_uzs - share
    booking.save()
    return booking


@transaction.atomic
def report_guide_no_show(booking: GuideBooking, *, now: datetime | None = None) -> GuideBooking:
    """Admin belgilaydi (turist shikoyati bo'yicha): gid kelmadi. Turistga 100%, gidga $25; 3 marta — blok."""
    now = now or timezone.now()
    booking = _locked(booking)
    if booking.status != GuideBooking.Status.CONFIRMED:
        raise ValidationError({"detail": "Faqat tasdiqlangan bron uchun."})
    booking.status = GuideBooking.Status.CANCELLED
    booking.no_show = GuideBooking.NoShow.GUIDE
    booking.cancelled_by = GuideBooking.CancelledBy.ADMIN
    booking.cancelled_at = now
    booking.cancel_reason = "Gid kelmadi"
    booking.refund_uzs = booking.total_uzs
    booking.guide_penalty_usd = policies.GUIDE_NO_SHOW_PENALTY_USD
    booking.save()

    guide = GuideProfile.objects.select_for_update().get(pk=booking.guide_id)
    guide.no_show_count += 1
    guide.save(update_fields=["no_show_count", "updated_at"])
    if guide.no_show_count >= policies.GUIDE_NO_SHOW_LIMIT and guide.status == GuideProfile.Status.APPROVED:
        suspend_profile(
            guide, f"{guide.no_show_count} marta kelmay qoldi. Qayta faollashtirish — intervyu orqali."
        )
    notify.guide_booking_cancelled(booking)
    user_events.guide_booking_cancelled(booking)
    return booking


# ---------- Fon vazifalari ----------


def expire_requests(*, now: datetime | None = None) -> int:
    now = now or timezone.now()
    count = 0
    qs = GuideBooking.objects.filter(status=GuideBooking.Status.REQUESTED, respond_by__lte=now)
    for booking in qs.select_related("guide", "user"):
        booking.status = GuideBooking.Status.EXPIRED
        booking.save(update_fields=["status", "updated_at"])
        user_events.guide_request_answered(booking)  # turistga: gid javob bermadi
        count += 1
    return count


def complete_finished(*, now: datetime | None = None) -> int:
    now = now or timezone.now()
    count = 0
    for b in GuideBooking.objects.filter(status=GuideBooking.Status.CONFIRMED, starts_at__lt=now):
        if b.starts_at + timedelta(days=b.days) <= now:
            b.status = GuideBooking.Status.COMPLETED
            b.save(update_fields=["status", "updated_at"])
            count += 1
    return count


# ---------- Sharhlar ----------


def recalculate_rating(guide_id: int) -> None:
    agg = GuideReview.objects.filter(guide_id=guide_id, is_published=True).aggregate(
        avg=Avg("rating"), n=Count("id")
    )
    rating = Decimal(str(agg["avg"] or 0)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    GuideProfile.objects.filter(pk=guide_id).update(rating=rating, reviews_count=agg["n"])
    guide = GuideProfile.objects.get(pk=guide_id)
    if (
        guide.status == GuideProfile.Status.APPROVED
        and guide.reviews_count >= policies.LOW_RATING_MIN_REVIEWS
        and guide.rating < policies.LOW_RATING_THRESHOLD
    ):
        suspend_profile(guide, f"Reyting {guide.rating} — 4.0 dan past. Vaqtincha to'xtatildi.")


@transaction.atomic
def create_review(*, user, booking: GuideBooking, rating: int, text: str = "") -> GuideReview:
    if booking.user_id != user.pk:
        raise ValidationError({"detail": "Bron topilmadi."})
    if booking.status != GuideBooking.Status.COMPLETED or booking.no_show == GuideBooking.NoShow.TOURIST:
        raise ValidationError({"detail": "Sharhni xizmat yakunlangandan keyin qoldirish mumkin."})
    if GuideReview.objects.filter(booking=booking).exists():
        raise ValidationError({"detail": "Bu bron uchun sharh allaqachon qoldirilgan."})
    review = GuideReview.objects.create(
        booking=booking, user=user, guide=booking.guide, rating=rating, text=text
    )  # is_published=False — admin tasdiqlagach saytga chiqadi
    notify.partner_review_created(review, booking.guide.display_name)
    return review
