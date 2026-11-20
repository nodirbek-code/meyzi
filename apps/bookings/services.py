"""
Bron biznes mantiqi. View'lar faqat shu funksiyalarni chaqiradi.

Joylar soni (`Departure.seats_booked`) faqat shu yerda o'zgaradi va doim `select_for_update`
bilan qulflangan sana ustida — bir vaqtdagi so'rovlar joyni ortiqcha sotib yubormasligi uchun.
"""

from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.agencies.models import Agency
from apps.notifications import services as notify
from apps.notifications import user_events
from apps.tours.models import Departure, Tour
from apps.tours.policies import refund_ratio

from .models import Booking, Traveler


def departure_datetime(departure: Departure) -> datetime:
    """Jo'nash sanasi + tur jo'nash vaqti (vaqt yo'q bo'lsa — kun boshi), Toshkent vaqti bilan."""
    naive = datetime.combine(departure.date, departure.tour.departure_time or time(0, 0))
    return timezone.make_aware(naive)


def _money(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), ROUND_HALF_UP))


def _release_seats(booking: Booking):
    Departure.objects.filter(pk=booking.departure_id).update(seats_booked=F("seats_booked") - booking.seats)


# ---------- Yaratish ----------


@transaction.atomic
def create_booking(
    *,
    user,
    departure_id: int,
    seats: int,
    contact_name: str,
    contact_phone: str,
    contact_email: str = "",
    note: str = "",
    travelers: list[dict] | None = None,
    now: datetime | None = None,
) -> Booking:
    now = now or timezone.now()
    travelers = travelers or []

    try:
        departure = (
            Departure.objects.select_for_update(of=("self",))
            .select_related("tour", "tour__agency")
            .get(pk=departure_id)
        )
    except Departure.DoesNotExist:
        raise ValidationError({"departure": "Bunday sana topilmadi."}) from None

    # Shu sanadagi muddati o'tgan bronlar joyini avval bo'shatamiz
    expire_due_bookings(now=now, departure_id=departure.pk)
    departure.refresh_from_db(fields=["seats_booked", "status"])

    tour = departure.tour
    if tour.status != Tour.Status.PUBLISHED or tour.agency.status != Agency.Status.ACTIVE:
        raise ValidationError({"departure": "Bu tur hozir sotuvda emas."})
    if departure.status != Departure.Status.OPEN:
        raise ValidationError({"departure": "Bu sanaga sotuv yopilgan."})

    departure_at = departure_datetime(departure)
    if departure_at <= now:
        raise ValidationError({"departure": "Bu sana o'tib ketgan."})
    if seats < 1:
        raise ValidationError({"seats": "Kamida 1 ta joy tanlang."})
    if seats > departure.seats_left:
        raise ValidationError({"seats": f"Bu sanada faqat {departure.seats_left} ta bo'sh joy qoldi."})
    if travelers and len(travelers) != seats:
        raise ValidationError(
            {"travelers": f"Sayohatchilar soni joylar soniga ({seats}) teng bo'lishi kerak."}
        )

    pending = Booking.objects.filter(
        user=user, status=Booking.Status.PENDING_PAYMENT, expires_at__gt=now
    ).count()
    if pending >= settings.LAZURI_MAX_PENDING_BOOKINGS:
        raise ValidationError(
            {"detail": "To'lanmagan bronlaringiz juda ko'p. Avval ularni to'lang yoki bekor qiling."}
        )

    unit_price = departure.effective_price
    total = unit_price * seats
    commission_percent = tour.agency.commission_percent
    commission = _money(Decimal(total) * commission_percent / 100)

    booking = Booking.objects.create(
        user=user,
        departure=departure,
        tour=tour,
        agency=tour.agency,
        seats=seats,
        unit_price_uzs=unit_price,
        total_uzs=total,
        commission_percent=commission_percent,
        commission_uzs=commission,
        agency_amount_uzs=total - commission,
        cancellation_policy=tour.cancellation_policy,
        departure_at=departure_at,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        note=note,
        expires_at=now + timedelta(minutes=settings.LAZURI_BOOKING_HOLD_MINUTES),
    )
    Traveler.objects.bulk_create(Traveler(booking=booking, **t) for t in travelers)
    Departure.objects.filter(pk=departure.pk).update(seats_booked=F("seats_booked") + seats)
    notify.booking_created(booking)
    user_events.tour_booking_created(booking)
    return booking


# ---------- Muddati o'tganlar ----------


@transaction.atomic
def expire_due_bookings(*, now: datetime | None = None, departure_id: int | None = None) -> int:
    """To'lov muddati o'tgan bronlarni `expired` qiladi va joylarni qaytaradi. Nechta bo'lganini qaytaradi."""
    now = now or timezone.now()
    qs = Booking.objects.select_for_update().filter(
        status=Booking.Status.PENDING_PAYMENT, expires_at__lte=now
    )
    if departure_id is not None:
        qs = qs.filter(departure_id=departure_id)
    count = 0
    for booking in qs:
        booking.status = Booking.Status.EXPIRED
        booking.save(update_fields=["status", "updated_at"])
        _release_seats(booking)
        count += 1
    return count


def refresh_if_expired(booking: Booking, now: datetime | None = None) -> Booking:
    """Bitta bronni o'qishdan oldin — muddati o'tgan bo'lsa darhol expired qiladi."""
    now = now or timezone.now()
    if booking.status == Booking.Status.PENDING_PAYMENT and booking.expires_at and booking.expires_at <= now:
        expire_due_bookings(now=now, departure_id=booking.departure_id)
        booking.refresh_from_db()
    return booking


# ---------- Tasdiqlash (to'lovdan keyin) ----------


@transaction.atomic
def confirm_booking(booking: Booking, *, now: datetime | None = None) -> Booking:
    """To'lov muvaffaqiyatli o'tganda chaqiriladi (5-bosqichda — to'lov provayderi webhook'idan)."""
    now = now or timezone.now()
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if booking.status == Booking.Status.CONFIRMED:
        return booking  # idempotent
    expired = booking.expires_at is not None and booking.expires_at <= now
    if booking.status != Booking.Status.PENDING_PAYMENT or expired:
        raise ValidationError({"detail": "Bron to'lov kutilayotgan holatda emas yoki muddati o'tgan."})
    booking.status = Booking.Status.CONFIRMED
    booking.confirmed_at = now
    booking.expires_at = None
    booking.save(update_fields=["status", "confirmed_at", "expires_at", "updated_at"])
    user_events.tour_booking_confirmed(booking)
    return booking


# ---------- Bekor qilish ----------


def refund_preview(booking: Booking, *, by: str, now: datetime | None = None) -> int:
    """Hozir bekor qilinsa qancha qaytariladi (so'm)."""
    now = now or timezone.now()
    if booking.status != Booking.Status.CONFIRMED:
        return 0  # hali to'lanmagan — qaytariladigan pul yo'q
    if by in (Booking.CancelledBy.AGENCY, Booking.CancelledBy.ADMIN):
        return booking.total_uzs  # tashkilotchi bekor qilsa — doim 100%
    ratio = refund_ratio(booking.cancellation_policy, booking.departure_at, now)
    return _money(Decimal(booking.total_uzs) * ratio)


@transaction.atomic
def cancel_booking(
    booking: Booking, *, by: str, reason: str = "", now: datetime | None = None, notify_admins: bool = True
) -> Booking:
    now = now or timezone.now()
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    refresh_if_expired(booking, now)
    if not booking.holds_seats:
        raise ValidationError(
            {"detail": f"Bronni bekor qilib bo'lmaydi: holati — {booking.get_status_display()}."}
        )
    if by == Booking.CancelledBy.TOURIST and booking.departure_at <= now:
        raise ValidationError({"detail": "Sayohat boshlangan — endi bekor qilib bo'lmaydi."})

    booking.refund_uzs = refund_preview(booking, by=by, now=now)
    booking.status = Booking.Status.CANCELLED
    booking.cancelled_at = now
    booking.cancelled_by = by
    booking.cancel_reason = reason
    booking.save()
    _release_seats(booking)
    if notify_admins:
        notify.booking_cancelled(booking)
    user_events.tour_booking_cancelled(booking)
    return booking


@transaction.atomic
def cancel_departure(departure: Departure, *, reason: str = "", now: datetime | None = None) -> int:
    """Agentlik sanani bekor qilsa — barcha faol bronlar 100% qaytarish bilan bekor qilinadi."""
    count = refund_total = 0
    for booking in Booking.objects.filter(departure=departure, status__in=Booking.ACTIVE_STATUSES):
        booking = cancel_booking(
            booking,
            by=Booking.CancelledBy.AGENCY,
            reason=reason or "Sana bekor qilindi",
            now=now,
            notify_admins=False,  # har bir bron emas — bitta umumiy xabar
        )
        count += 1
        refund_total += booking.refund_uzs
    if count:
        notify.departure_cancelled(departure, count, refund_total)
    return count


# ---------- Yakunlash ----------


def complete_finished_bookings(*, now: datetime | None = None) -> int:
    """Sayohat tugagan (jo'nash + davomiylik) tasdiqlangan bronlarni `completed` qiladi."""
    now = now or timezone.now()
    count = 0
    qs = Booking.objects.filter(status=Booking.Status.CONFIRMED, departure_at__lt=now).select_related("tour")
    for booking in qs:
        if booking.departure_at + timedelta(days=booking.tour.duration_days) <= now:
            booking.status = Booking.Status.COMPLETED
            booking.save(update_fields=["status", "updated_at"])
            count += 1
    return count
