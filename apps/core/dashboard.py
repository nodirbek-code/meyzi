"""Admin dashboard ma'lumotlari: tekshiruv navbati, pul, ogohlantirishlar, platforma holati.

Admin barcha vazifalarni shu sahifadan boshlaydi: har bir karta tegishli (filtrlangan) ro'yxatga olib boradi,
u yerda ✅ Tasdiqlash / ↩️ Qaytarish amallari bor.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone


@dataclass
class QueueItem:
    title: str
    icon: str
    count: int
    url: str
    oldest: str  # "3 kun", "5 soat"
    overdue: bool  # 24 soatdan ko'p kutyapti


def _age(dt) -> tuple[str, bool]:
    if dt is None:
        return "", False
    delta = timezone.now() - dt
    hours = int(delta.total_seconds() // 3600)
    text = f"{hours // 24} kun" if hours >= 24 else f"{hours} soat" if hours else "hozirgina"
    return text, hours >= 24


def _changelist(model, query: str = "") -> str:
    meta = model._meta
    return reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist") + (f"?{query}" if query else "")


def moderation_queue() -> list[QueueItem]:
    from apps.agencies.models import Agency, AgencyApplication
    from apps.guides.models import GuideProfile, GuideReview
    from apps.hotels.models import Hotel, HotelReview
    from apps.reviews.models import Review
    from apps.tours.models import Tour

    rows = [
        (
            "Agentlik arizalari",
            "🏢",
            AgencyApplication.objects.filter(status="new"),
            "status__exact=new",
            "created_at",
        ),
        (
            "Mehmonxonalar",
            "🏨",
            Hotel.objects.filter(status="pending"),
            "status__exact=pending",
            "updated_at",
        ),
        (
            "Gidlar",
            "🧑‍💼",
            GuideProfile.objects.filter(status="pending"),
            "status__exact=pending",
            "updated_at",
        ),
        (
            "Turlar",
            "🧭",
            Tour.objects.filter(status="pending_review"),
            "status__exact=pending_review",
            "updated_at",
        ),
        (
            "Agentlik profillari",
            "📝",
            Agency.objects.filter(moderation_status="pending"),
            "moderation_status__exact=pending",
            "updated_at",
        ),
        (
            "Tur sharhlari",
            "💬",
            Review.objects.filter(status="pending"),
            "status__exact=pending",
            "created_at",
        ),
        (
            "Mehmonxona sharhlari",
            "💬",
            HotelReview.objects.filter(is_moderated=False),
            "is_moderated__exact=0",
            "created_at",
        ),
        (
            "Gid sharhlari",
            "💬",
            GuideReview.objects.filter(is_moderated=False),
            "is_moderated__exact=0",
            "created_at",
        ),
    ]
    items = []
    for title, icon, qs, query, date_field in rows:
        count = qs.count()
        oldest = qs.order_by(date_field).values_list(date_field, flat=True).first() if count else None
        age, overdue = _age(oldest)
        items.append(QueueItem(title, icon, count, _changelist(qs.model, query), age, overdue))
    return items


def _booking_models():
    from apps.bookings.models import Booking
    from apps.guides.models import GuideBooking
    from apps.hotels.models import HotelBooking

    return (("Turlar", Booking), ("Mehmonxonalar", HotelBooking), ("Gidlar", GuideBooking))


PAID = ("confirmed", "completed")


def money(days: int = 30) -> dict:
    """Bugun / 7 kun / 30 kun: to'langan bronlar, aylanma, platforma komissiyasi; kunlik komissiya grafigi."""
    now = timezone.now()
    today = timezone.localdate()
    start_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    periods = {"today": start_today, "week": now - timedelta(days=7), "month": now - timedelta(days=days)}
    out = {k: {"count": 0, "total": 0, "commission": 0} for k in periods}
    by_kind = []
    daily: dict = {}
    pending_payment = 0
    new_today = 0
    cancelled_today = 0
    for label, model in _booking_models():
        paid = model.objects.filter(status__in=PAID, confirmed_at__isnull=False)
        for key, since in periods.items():
            agg = paid.filter(confirmed_at__gte=since).aggregate(
                n=Count("id"), total=Sum("total_uzs"), commission=Sum("commission_uzs")
            )
            out[key]["count"] += agg["n"] or 0
            out[key]["total"] += agg["total"] or 0
            out[key]["commission"] += agg["commission"] or 0
        month = paid.filter(confirmed_at__gte=periods["month"]).aggregate(
            n=Count("id"), commission=Sum("commission_uzs")
        )
        by_kind.append({"label": label, "count": month["n"] or 0, "commission": month["commission"] or 0})
        for row in (
            paid.filter(confirmed_at__gte=now - timedelta(days=13))
            .annotate(day=TruncDate("confirmed_at"))
            .values("day")
            .annotate(c=Sum("commission_uzs"))
        ):
            daily[row["day"]] = daily.get(row["day"], 0) + (row["c"] or 0)
        waiting = Q(status="pending_payment") | Q(status="accepted")
        pending_payment += model.objects.filter(waiting).count()
        new_today += model.objects.filter(created_at__gte=start_today).count()
        cancelled_today += model.objects.filter(status="cancelled", cancelled_at__gte=start_today).count()

    chart = []
    peak = max(daily.values(), default=0) or 1
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        value = daily.get(d, 0)
        chart.append({"day": d, "value": value, "pct": round(value * 100 / peak)})
    return {
        **out,
        "by_kind": by_kind,
        "chart": chart,
        "pending_payment": pending_payment,
        "new_today": new_today,
        "cancelled_today": cancelled_today,
    }


def alerts() -> list[dict]:
    """Admin e'tiborini talab qiladigan holatlar (bo'sh bo'lsa — hammasi joyida)."""
    from apps.agencies.models import Agency
    from apps.guides.models import GuideBooking, GuideProfile
    from apps.hotels.models import Hotel

    items = []
    low = [
        ("Reytingi past mehmonxonalar", Hotel.objects.filter(status="approved"), Hotel),
        ("Reytingi past gidlar", GuideProfile.objects.filter(status="approved"), GuideProfile),
        ("Reytingi past agentliklar", Agency.objects.filter(status="active"), Agency),
    ]
    for title, qs, model in low:
        n = qs.filter(reviews_count__gte=3, rating__lt=4).count()
        if n:
            items.append({"text": f"{title} (4.0 dan past): {n} ta", "url": _changelist(model)})
    late = GuideBooking.objects.filter(status="requested", respond_by__lt=timezone.now()).count()
    if late:
        items.append(
            {
                "text": f"Gid javob bermagan so'rovlar: {late} ta",
                "url": _changelist(GuideBooking, "status__exact=requested"),
            }
        )
    suspended = (
        Hotel.objects.filter(status="suspended").count()
        + GuideProfile.objects.filter(status="suspended").count()
        + Agency.objects.filter(status="suspended").count()
    )
    if suspended:
        items.append({"text": f"To'xtatilgan hamkorlar: {suspended} ta", "url": ""})
    return items


def platform() -> list[dict]:
    from apps.accounts.models import User
    from apps.agencies.models import Agency
    from apps.guides.models import GuideProfile
    from apps.hotels.models import Hotel
    from apps.tours.models import Tour

    today = timezone.localdate()
    return [
        {
            "label": "Saytdagi turlar",
            "value": Tour.objects.filter(status="published").count(),
            "url": _changelist(Tour, "status__exact=published"),
        },
        {
            "label": "Agentliklar",
            "value": Agency.objects.filter(status="active").count(),
            "url": _changelist(Agency),
        },
        {
            "label": "Mehmonxonalar",
            "value": Hotel.objects.filter(status="approved").count(),
            "url": _changelist(Hotel, "status__exact=approved"),
        },
        {
            "label": "Gidlar",
            "value": GuideProfile.objects.filter(status="approved").count(),
            "url": _changelist(GuideProfile, "status__exact=approved"),
        },
        {"label": "Foydalanuvchilar", "value": User.objects.count(), "url": _changelist(User)},
        {
            "label": "Bugun ro'yxatdan o'tdi",
            "value": User.objects.filter(date_joined__date=today).count(),
            "url": _changelist(User),
        },
    ]


def recent_actions(limit: int = 12):
    from django.contrib.admin.models import LogEntry

    return LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:limit]


def context() -> dict:
    queue = moderation_queue()
    return {
        "queue": queue,
        "queue_total": sum(i.count for i in queue),
        "money": money(),
        "alerts": alerts(),
        "platform": platform(),
        "recent_actions": recent_actions(),
    }
