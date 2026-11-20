"""Mehmonxonalar — bo'sh xonalar, bron, bekor qilish, sharhlar."""

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.notifications import services as notify
from apps.tours.policies import refund_ratio

from .models import Hotel, HotelBooking, HotelMember, HotelReview, RoomType

MAX_NIGHTS = 30


def _money(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), ROUND_HALF_UP))


def unique_hotel_slug(name: str) -> str:
    base = slugify(name) or "hotel"
    slug, n = base, 2
    while Hotel.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


# ---------- Ariza ----------


@transaction.atomic
def register_hotel(*, user, **fields) -> Hotel:
    if HotelMember.objects.filter(user=user).exists():
        raise ValidationError({"detail": "Siz allaqachon mehmonxonaga biriktirilgansiz."})
    hotel = Hotel.objects.create(
        slug=unique_hotel_slug(fields["name"]), status=Hotel.Status.PENDING, **fields
    )
    HotelMember.objects.create(hotel=hotel, user=user, role=HotelMember.Role.OWNER)
    if user.role == User.Role.TOURIST:
        user.role = User.Role.BUSINESS
        user.save(update_fields=["role"])
    notify.hotel_application(hotel)
    return hotel


def approve_hotel(hotel: Hotel) -> Hotel:
    hotel.status = Hotel.Status.APPROVED
    hotel.moderation_note = ""
    hotel.save(update_fields=["status", "moderation_note", "updated_at"])
    return hotel


# ---------- Bo'sh xonalar ----------


def _active_overlapping(room_type_ids, check_in: date, check_out: date, now: datetime, exclude_id=None):
    qs = HotelBooking.objects.filter(
        room_type_id__in=room_type_ids, check_in__lt=check_out, check_out__gt=check_in
    ).filter(
        Q(status=HotelBooking.Status.CONFIRMED)
        | Q(status=HotelBooking.Status.PENDING_PAYMENT, expires_at__gt=now)  # eskirgan ushlab turmaydi
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.only("room_type_id", "check_in", "check_out", "rooms")


def availability(room_types, check_in: date, check_out: date, now: datetime | None = None) -> dict[int, int]:
    """{room_type_id: shu oraliqning har kechasida bo'sh xonalar soni (minimum)}."""
    now = now or timezone.now()
    room_types = list(room_types)
    nights = [check_in + timedelta(days=i) for i in range((check_out - check_in).days)]
    used = {rt.pk: dict.fromkeys(nights, 0) for rt in room_types}
    for b in _active_overlapping([rt.pk for rt in room_types], check_in, check_out, now):
        for night in nights:
            if b.check_in <= night < b.check_out:
                used[b.room_type_id][night] += b.rooms
    return {rt.pk: max(rt.total_rooms - max(used[rt.pk].values(), default=0), 0) for rt in room_types}


def validate_stay(check_in: date, check_out: date) -> int:
    if check_in < timezone.localdate():
        raise ValidationError({"check_in": "O'tgan sana."})
    nights = (check_out - check_in).days
    if nights < 1:
        raise ValidationError({"check_out": "Chiqish kirishdan keyin bo'lishi kerak."})
    if nights > MAX_NIGHTS:
        raise ValidationError({"check_out": f"Ko'pi bilan {MAX_NIGHTS} kecha."})
    return nights


# ---------- Bron ----------


@transaction.atomic
def create_booking(
    *,
    user,
    room_type_id: int,
    check_in: date,
    check_out: date,
    rooms: int,
    guests: int,
    contact_name: str,
    contact_phone: str,
    contact_email: str = "",
    note: str = "",
    now: datetime | None = None,
) -> HotelBooking:
    now = now or timezone.now()
    try:
        room_type = (
            RoomType.objects.select_for_update(of=("self",)).select_related("hotel").get(pk=room_type_id)
        )
    except RoomType.DoesNotExist:
        raise ValidationError({"room_type": "Xona turi topilmadi."}) from None
    hotel = room_type.hotel
    if not hotel.is_approved or not room_type.is_active:
        raise ValidationError({"room_type": "Bu xona hozir bron qilinmaydi."})

    nights = validate_stay(check_in, check_out)
    if rooms < 1:
        raise ValidationError({"rooms": "Kamida 1 xona."})
    if guests < 1 or guests > room_type.capacity * rooms:
        raise ValidationError(
            {"guests": f"{rooms} ta xonaga ko'pi bilan {room_type.capacity * rooms} kishi."}
        )

    free = availability([room_type], check_in, check_out, now)[room_type.pk]
    if rooms > free:
        raise ValidationError({"rooms": f"Bu sanalarda faqat {free} ta bo'sh xona bor."})

    pending = HotelBooking.objects.filter(
        user=user, status=HotelBooking.Status.PENDING_PAYMENT, expires_at__gt=now
    ).count()
    if pending >= settings.LAZURI_MAX_PENDING_BOOKINGS:
        raise ValidationError({"detail": "To'lanmagan bronlaringiz juda ko'p."})

    total = room_type.price_per_night_uzs * nights * rooms
    commission = _money(Decimal(total) * hotel.commission_percent / 100)
    booking = HotelBooking.objects.create(
        user=user,
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        rooms=rooms,
        guests=guests,
        check_in_at=timezone.make_aware(datetime.combine(check_in, hotel.check_in_time)),
        price_per_night_uzs=room_type.price_per_night_uzs,
        total_uzs=total,
        commission_percent=hotel.commission_percent,
        commission_uzs=commission,
        hotel_amount_uzs=total - commission,
        cancellation_policy=hotel.cancellation_policy,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        note=note,
        expires_at=now + timedelta(minutes=settings.LAZURI_BOOKING_HOLD_MINUTES),
    )
    notify.hotel_booking_created(booking)
    return booking


def _locked(booking: HotelBooking) -> HotelBooking:
    return HotelBooking.objects.select_for_update().get(pk=booking.pk)


def refresh_if_expired(booking: HotelBooking, now: datetime | None = None) -> HotelBooking:
    now = now or timezone.now()
    if (
        booking.status == HotelBooking.Status.PENDING_PAYMENT
        and booking.expires_at
        and booking.expires_at <= now
    ):
        HotelBooking.objects.filter(pk=booking.pk, status=HotelBooking.Status.PENDING_PAYMENT).update(
            status=HotelBooking.Status.EXPIRED
        )
        booking.refresh_from_db()
    return booking


@transaction.atomic
def mark_paid(booking: HotelBooking, *, now: datetime | None = None) -> HotelBooking:
    now = now or timezone.now()
    booking = refresh_if_expired(_locked(booking), now)
    if booking.status == HotelBooking.Status.CONFIRMED:
        return booking
    if booking.status != HotelBooking.Status.PENDING_PAYMENT:
        raise ValidationError({"detail": f"Tasdiqlab bo'lmaydi: holati — {booking.get_status_display()}."})
    booking.status = HotelBooking.Status.CONFIRMED
    booking.confirmed_at = now
    booking.expires_at = None
    booking.save(update_fields=["status", "confirmed_at", "expires_at", "updated_at"])
    return booking


def refund_preview(booking: HotelBooking, *, by: str, now: datetime | None = None) -> int:
    now = now or timezone.now()
    if booking.status != HotelBooking.Status.CONFIRMED:
        return 0
    if by in (HotelBooking.CancelledBy.HOTEL, HotelBooking.CancelledBy.ADMIN):
        return booking.total_uzs
    return _money(
        Decimal(booking.total_uzs) * refund_ratio(booking.cancellation_policy, booking.check_in_at, now)
    )


@transaction.atomic
def cancel(booking: HotelBooking, *, by: str, reason: str = "", now: datetime | None = None) -> HotelBooking:
    now = now or timezone.now()
    booking = refresh_if_expired(_locked(booking), now)
    if booking.status not in HotelBooking.ACTIVE_STATUSES:
        raise ValidationError({"detail": f"Bekor qilib bo'lmaydi: holati — {booking.get_status_display()}."})
    if by == HotelBooking.CancelledBy.TOURIST and booking.check_in_at <= now:
        raise ValidationError({"detail": "Kirish vaqti o'tgan — bekor qilib bo'lmaydi."})
    booking.refund_uzs = refund_preview(booking, by=by, now=now)
    booking.status = HotelBooking.Status.CANCELLED
    booking.cancelled_at = now
    booking.cancelled_by = by
    booking.cancel_reason = reason
    booking.save()
    notify.hotel_booking_cancelled(booking)
    return booking


# ---------- Fon vazifalari ----------


def expire_due(*, now: datetime | None = None) -> int:
    now = now or timezone.now()
    return HotelBooking.objects.filter(
        status=HotelBooking.Status.PENDING_PAYMENT, expires_at__lte=now
    ).update(status=HotelBooking.Status.EXPIRED, updated_at=now)


def complete_finished(*, today: date | None = None) -> int:
    today = today or timezone.localdate()
    return HotelBooking.objects.filter(status=HotelBooking.Status.CONFIRMED, check_out__lte=today).update(
        status=HotelBooking.Status.COMPLETED
    )


# ---------- Sharhlar ----------


def recalculate_rating(hotel_id: int) -> None:
    agg = HotelReview.objects.filter(hotel_id=hotel_id, is_published=True).aggregate(
        avg=Avg("rating"), n=Count("id")
    )
    rating = Decimal(str(agg["avg"] or 0)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    Hotel.objects.filter(pk=hotel_id).update(rating=rating, reviews_count=agg["n"])


@transaction.atomic
def create_review(*, user, booking: HotelBooking, rating: int, text: str = "") -> HotelReview:
    if booking.user_id != user.pk:
        raise ValidationError({"detail": "Bron topilmadi."})
    if booking.status != HotelBooking.Status.COMPLETED:
        raise ValidationError({"detail": "Sharhni yashab bo'lgandan keyin qoldirish mumkin."})
    if HotelReview.objects.filter(booking=booking).exists():
        raise ValidationError({"detail": "Bu bron uchun sharh allaqachon qoldirilgan."})
    review = HotelReview.objects.create(
        booking=booking, user=user, hotel=booking.hotel, rating=rating, text=text
    )
    recalculate_rating(booking.hotel_id)
    return review
