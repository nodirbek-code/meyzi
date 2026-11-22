from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.agencies.models import Agency
from apps.bookings.models import Booking
from apps.notifications import services as notify
from apps.tours.models import Tour

from .models import Review


def _stats(qs) -> tuple[Decimal, int]:
    agg = qs.filter(status=Review.Status.PUBLISHED).aggregate(avg=Avg("rating"), n=Count("id"))
    avg = Decimal(str(agg["avg"] or 0)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return avg, agg["n"]


def recalculate_ratings(*, tour_id: int, agency_id: int) -> None:
    """Tur va agentlik keshlangan reytingini faqat e'lon qilingan sharhlardan qayta hisoblaydi."""
    rating, count = _stats(Review.objects.filter(tour_id=tour_id))
    Tour.objects.filter(pk=tour_id).update(rating=rating, reviews_count=count)
    rating, count = _stats(Review.objects.filter(agency_id=agency_id))
    Agency.objects.filter(pk=agency_id).update(rating=rating, reviews_count=count)


@transaction.atomic
def create_review(*, user, booking_code: str, rating: int, text: str = "") -> Review:
    try:
        booking = Booking.objects.select_related("tour", "agency").get(code=booking_code, user=user)
    except Booking.DoesNotExist:
        raise ValidationError({"booking": "Bron topilmadi."}) from None
    if booking.status != Booking.Status.COMPLETED:
        raise ValidationError({"booking": "Sharhni sayohat yakunlangandan keyin qoldirish mumkin."})
    if Review.objects.filter(booking=booking).exists():
        raise ValidationError({"booking": "Bu bron uchun sharh allaqachon qoldirilgan."})

    review = Review.objects.create(
        booking=booking, user=user, tour=booking.tour, agency=booking.agency, rating=rating, text=text
    )  # status=PENDING — admin tasdiqlagach saytga chiqadi
    notify.review_created(review)
    return review


@transaction.atomic
def update_review(review: Review, *, rating: int | None = None, text: str | None = None) -> Review:
    if rating is not None:
        review.rating = rating
    if text is not None:
        review.text = text
    review.status = Review.Status.PENDING  # o'zgartirilgan sharh ham qayta tekshiruvga
    review.save()
    recalculate_ratings(tour_id=review.tour_id, agency_id=review.agency_id)
    return review


@transaction.atomic
def set_status(review: Review, status: str, note: str = "") -> Review:
    review.status = status
    review.moderation_note = note
    review.save(update_fields=["status", "moderation_note", "updated_at"])
    recalculate_ratings(tour_id=review.tour_id, agency_id=review.agency_id)
    return review


def agency_reply(review: Review, text: str) -> Review:
    review.agency_reply = text
    review.agency_replied_at = timezone.now() if text else None
    review.save(update_fields=["agency_reply", "agency_replied_at", "updated_at"])
    return review
