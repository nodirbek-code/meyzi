"""Saytdagi admin paneli (/control) uchun API — faqat adminlar (is_staff).

Admin hamkor ma'lumotlarini O'ZGARTIRMAYDI: faqat ko'radi va qaror qiladi —
✅ tasdiqlash, ↩️ izoh bilan qaytarish, ⛔ to'xtatish / ▶️ faollashtirish. Har bir amal tarixga yoziladi.

Turlar (kind): hotel, guide, tour, agency (profil o'zgarishlari), application (agentlik arizasi),
review (tur sharhi), hotel_review, guide_review.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import authenticate
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from . import dashboard

BAD_LOGIN = "Email yoki parol noto'g'ri."


class IsStaff(permissions.BasePermission):
    message = "Bu bo'lim faqat adminlar uchun."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


# ---------- Kirish ----------


class ControlLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})


class ControlLoginView(APIView):
    """Admin kirishi (Django admin email + paroli). Admin bo'lmaganlarga ham bir xil xato."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(request=ControlLoginSerializer, responses={200: dict})
    def post(self, request):
        from apps.accounts.views import _tokens

        ser = ControlLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(
            request,
            email=ser.validated_data["email"].strip().lower(),
            password=ser.validated_data["password"],
        )
        if user is None or not user.is_active or not user.is_staff:
            raise ValidationError({"detail": BAD_LOGIN})
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return Response(_tokens(user, request))


# ---------- Turlar ro'yxati (registry) ----------


def _url(request, f) -> str | None:
    if not f:
        return None
    try:
        return request.build_absolute_uri(f.url)
    except ValueError:
        return None


def _log(request, obj, message: str) -> None:
    LogEntry.objects.log_actions(
        user_id=request.user.pk,
        queryset=[obj],
        action_flag=CHANGE,
        change_message=message,
        single_object=True,
    )


@dataclass
class Kind:
    title: str
    icon: str
    queryset: Callable
    states: dict  # state → filter kwargs
    row: Callable  # obj → {title, subtitle}
    detail: Callable  # (obj, request) → dict
    approve: Callable | None = None
    reject: Callable | None = None  # (obj, note)
    suspend: Callable | None = None
    activate: Callable | None = None
    status_of: Callable = field(default=lambda o: getattr(o, "status", ""))
    waiting_field: str = "updated_at"
    public_url: Callable = field(default=lambda o: None)
    area: str = ""  # "hotels" | "guides" — soha moderatori ko'radi; bo'sh — faqat asosiy admin
    two_stage: bool = False  # moderator tekshiradi → asosiy admin yakuniy tasdiqlaydi


def _hotel_kind() -> Kind:
    from apps.hotels import services
    from apps.hotels.models import Hotel
    from apps.hotels.serializers import HotelImageSerializer, MyHotelSerializer, RoomTypeSerializer
    from apps.notifications import user_events

    def detail(h, request):
        ctx = {"request": request}
        return {
            **MyHotelSerializer(h, context=ctx).data,
            "destination_name": h.destination.name,
            "media": HotelImageSerializer(h.images.all(), many=True, context=ctx).data,
            "rooms": RoomTypeSerializer(h.room_types.all(), many=True, context=ctx).data,
            "members": [
                {"email": m.user.email, "phone": m.user.phone, "role": m.role}
                for m in h.members.select_related("user")
            ],
        }

    def set_status(h, value):
        h.status = value
        h.save(update_fields=["status", "updated_at"])
        user_events.hotel_status(h)

    return Kind(
        "Mehmonxonalar",
        "🏨",
        lambda: Hotel.objects.select_related("destination"),
        {
            "pending": {"status": "pending"},
            "rejected": {"status": "rejected"},
            "approved": {"status": "approved"},
            "suspended": {"status": "suspended"},
        },
        lambda h: {"title": h.name, "subtitle": f"{h.destination.name} · {h.get_kind_display()}"},
        detail,
        approve=services.approve_hotel,
        reject=services.reject_hotel,
        suspend=lambda h: set_status(h, Hotel.Status.SUSPENDED),
        activate=services.approve_hotel,
        public_url=lambda h: f"/hotels/{h.slug}",
    )


def _guide_kind() -> Kind:
    from apps.guides import services
    from apps.guides.models import GuideProfile
    from apps.guides.serializers import MeetingPointSerializer, MyGuideProfileSerializer

    def detail(g, request):
        ctx = {"request": request}
        data = MyGuideProfileSerializer(g, context=ctx).data
        return {
            **data,
            "destination_names": [d.name for d in g.destinations.all()],
            "email": g.user.email,
            "certificate_url": f"/control/items/guide/{g.pk}/certificate" if g.certificate_file else None,
            "meeting_points": MeetingPointSerializer(g.meeting_points.all(), many=True, context=ctx).data,
        }

    return Kind(
        "Gidlar",
        "🧑‍💼",
        lambda: GuideProfile.objects.select_related("user"),
        {
            "pending": {"status": "pending"},
            "rejected": {"status": "rejected"},
            "approved": {"status": "approved"},
            "suspended": {"status": "suspended"},
        },
        lambda g: {"title": g.display_name, "subtitle": ", ".join(g.languages)},
        detail,
        approve=services.approve_profile,
        reject=services.reject_profile,
        suspend=lambda g: services.suspend_profile(g, "Admin to'xtatdi"),
        activate=services.approve_profile,
        public_url=lambda g: f"/guides/{g.slug}",
    )


def _tour_kind() -> Kind:
    from apps.notifications import user_events
    from apps.tours.models import Tour
    from apps.tours.serializers import CabinetTourSerializer, DepartureSerializer
    from apps.tours.views import reject_tour

    def approve(t):
        t.publish()
        t.moderation_note = ""
        t.save()
        user_events.tour_moderated(t)

    def detail(t, request):
        ctx = {"request": request}
        return {
            **CabinetTourSerializer(t, context=ctx).data,
            "agency_name": t.agency.name,
            "destination_name": t.destination.name,
            "departures": DepartureSerializer(
                t.departures.order_by("date")[:30], many=True, context=ctx
            ).data,
        }

    return Kind(
        "Turlar",
        "🧭",
        lambda: Tour.objects.select_related("agency", "destination"),
        {
            "pending": {"status": "pending_review"},
            "rejected": {"status": "rejected"},
            "approved": {"status": "published"},
        },
        lambda t: {"title": t.title, "subtitle": f"{t.agency.name} · {t.destination.name}"},
        detail,
        approve=approve,
        reject=reject_tour,
        status_of=lambda t: {"pending_review": "pending", "published": "approved"}.get(t.status, t.status),
        public_url=lambda t: f"/tours/{t.slug}",
    )


def _agency_kind() -> Kind:
    from apps.agencies import services
    from apps.agencies.models import Agency
    from apps.agencies.serializers import CabinetAgencySerializer

    def detail(a, request):
        return {
            **CabinetAgencySerializer(a, context={"request": request}).data,
            "members": [
                {"email": m.user.email, "phone": m.user.phone, "role": m.role}
                for m in a.members.select_related("user")
            ],
        }

    def set_status(a, value):
        a.status = value
        a.save(update_fields=["status", "updated_at"])

    return Kind(
        "Agentlik profillari",
        "🏢",
        lambda: Agency.objects.all(),
        {
            "pending": {"moderation_status": "pending"},
            "rejected": {"moderation_status": "rejected"},
            "approved": {"moderation_status": "approved"},
            "suspended": {"status": "suspended"},
        },
        lambda a: {"title": a.name, "subtitle": a.phone or a.email},
        detail,
        approve=services.approve_agency,
        reject=services.return_agency,
        suspend=lambda a: set_status(a, Agency.Status.SUSPENDED),
        activate=lambda a: set_status(a, Agency.Status.ACTIVE),
        status_of=lambda a: "suspended" if a.status == "suspended" else a.moderation_status,
        public_url=lambda a: f"/agencies/{a.slug}",
    )


def _application_kind() -> Kind:
    from apps.agencies.models import AgencyApplication

    def detail(a, request):
        return {
            "agency_name": a.agency_name,
            "contact_person": a.contact_person,
            "phone": a.phone,
            "email": a.email,
            "message": a.message,
            "account_email": a.user.email if a.user else None,
            "status": a.status,
            "moderation_note": a.admin_note,
            "created_at": a.created_at,
        }

    return Kind(
        "Agentlik arizalari",
        "📨",
        lambda: AgencyApplication.objects.select_related("user"),
        {
            "pending": {"status__in": ["new", "in_review"]},
            "rejected": {"status": "rejected"},
            "approved": {"status": "approved"},
        },
        lambda a: {"title": a.agency_name, "subtitle": f"{a.contact_person} · {a.phone}"},
        detail,
        approve=None,  # request.user kerak — view ichida
        reject=None,
        status_of=lambda a: {"new": "pending", "in_review": "pending"}.get(a.status, a.status),
        waiting_field="created_at",
    )


def _review_detail(r, about: str, reply: str) -> dict:
    u = r.user
    return {
        "about": about,
        "author": f"{u.first_name} {u.last_name}".strip() or u.email or u.phone,
        "rating": r.rating,
        "text": r.text,
        "reply": reply,
        "created_at": r.created_at,
    }


def _review_kind() -> Kind:
    from apps.reviews import services
    from apps.reviews.models import Review

    return Kind(
        "Tur sharhlari",
        "💬",
        lambda: Review.objects.select_related("tour", "user"),
        {
            "pending": {"status": "pending"},
            "rejected": {"status": "hidden"},
            "approved": {"status": "published"},
        },
        lambda r: {"title": f"{'★' * r.rating} {r.tour.title}", "subtitle": (r.text or "—")[:120]},
        lambda r, request: {**_review_detail(r, r.tour.title, r.agency_reply), "status": r.status},
        approve=lambda r: services.set_status(r, Review.Status.PUBLISHED),
        reject=lambda r, note: services.set_status(r, Review.Status.HIDDEN, note=note[:255]),
        status_of=lambda r: {"published": "approved", "hidden": "rejected"}.get(r.status, r.status),
        waiting_field="created_at",
    )


def _partner_review_kind(app: str) -> Kind:
    if app == "hotels":
        from apps.hotels import services
        from apps.hotels.models import HotelReview as M

        title, about, reply = "Mehmonxona sharhlari", (lambda r: r.hotel.name), "hotel_reply"
        related = "hotel"
    else:
        from apps.guides import services
        from apps.guides.models import GuideReview as M

        title, about, reply = "Gid sharhlari", (lambda r: r.guide.display_name), "guide_reply"
        related = "guide"

    def state(r):
        if not r.is_moderated:
            return "pending"
        return "approved" if r.is_published else "rejected"

    return Kind(
        title,
        "💬",
        lambda: M.objects.select_related(related, "user"),
        {
            "pending": {"is_moderated": False},
            "rejected": {"is_moderated": True, "is_published": False},
            "approved": {"is_published": True},
        },
        lambda r: {"title": f"{'★' * r.rating} {about(r)}", "subtitle": (r.text or "—")[:120]},
        lambda r, request: {**_review_detail(r, about(r), getattr(r, reply)), "status": state(r)},
        approve=lambda r: services.set_review_published(r, True),
        reject=lambda r, note: services.set_review_published(r, False),
        status_of=state,
        waiting_field="created_at",
    )


def kinds() -> dict[str, Kind]:
    return {
        "application": _application_kind(),
        "hotel": _hotel_kind(),
        "guide": _guide_kind(),
        "tour": _tour_kind(),
        "agency": _agency_kind(),
        "review": _review_kind(),
        "hotel_review": _partner_review_kind("hotels"),
        "guide_review": _partner_review_kind("guides"),
    }


def _kind(name: str) -> Kind:
    k = kinds().get(name)
    if k is None:
        raise Http404
    return k


# ---------- View'lar ----------


# ---------- Rollar: asosiy admin va soha moderatorlari ----------

REVIEW_KINDS = ("review", "hotel_review", "guide_review")
# Hamkorlik arizalarini Excel'dan qo'shish: navbat turi → import bo'limi (control_crud.application_resources)
APPLICATION_IMPORTS = {
    "application": "agency_application",
    "guide": "guide_application",
    "hotel": "hotel_application",
}
AREA_TITLE = {"hotels": "Mehmonxonalar moderatori", "guides": "Gidlar moderatori", "admin": "Asosiy admin"}


def staff_role(user) -> str:
    """ "admin" (asosiy admin) | "hotels" | "guides" (soha moderatori)."""
    if user.is_superuser or not getattr(user, "staff_area", ""):
        return "admin"
    return user.staff_area


class IsMainAdmin(IsStaff):
    message = "Bu bo'lim faqat asosiy admin uchun."

    def has_permission(self, request, view):
        return super().has_permission(request, view) and staff_role(request.user) == "admin"


def _two_stage(k: Kind, area: str) -> Kind:
    """Ikki bosqich: "precheck" — moderatorda, "pending" — moderator tekshirdi, admin tasdig'ida."""
    k.area, k.two_stage = area, True
    rest = {s: f for s, f in k.states.items() if s != "pending"}
    k.states = {
        "precheck": {"status": "pending", "prechecked_at__isnull": True},
        "pending": {"status": "pending", "prechecked_at__isnull": False},
        **rest,
    }
    base = k.status_of
    k.status_of = lambda o: (
        ("pending" if o.prechecked_at else "precheck") if o.status == "pending" else base(o)
    )
    return k


def visible_kinds(user) -> dict[str, Kind]:
    role = staff_role(user)
    ks = kinds()
    _two_stage(ks["hotel"], "hotels")
    _two_stage(ks["guide"], "guides")
    ks["hotel_review"].area = "hotels"
    ks["guide_review"].area = "guides"
    if role == "admin":
        return ks
    return {name: k for name, k in ks.items() if k.area == role}


def _visible_kind(request, name: str) -> Kind:
    k = visible_kinds(request.user).get(name)
    if k is None:
        raise Http404
    return k


def actionable_state(k: Kind, role: str) -> str:
    """Navbatdagi "ish kutayotgan" holat: moderatorga — precheck, adminga — pending (moderator tekshirgan)."""
    if k.two_stage and role != "admin":
        return "precheck"
    return "pending"


def allowed_actions(name: str, k: Kind, obj, role: str) -> list[str]:
    state = k.status_of(obj)
    if role == "admin":
        acts = []
        if state != "approved":
            acts.append("approve")
        if k.two_stage and state == "precheck":
            acts.append("precheck")
        if name in REVIEW_KINDS:
            if state != "rejected":
                acts.append("return")
        else:
            acts.append("return")
        if k.suspend is not None:
            acts.append("activate" if state == "suspended" else "suspend")
        return acts
    if name in REVIEW_KINDS:  # sharhlar — soha moderatori o'zi hal qiladi
        return [a for a, ok in (("approve", state != "approved"), ("return", state != "rejected")) if ok]
    if k.two_stage and state == "precheck":
        return ["precheck", "return"]
    return []


def _precheck_info(obj) -> dict | None:
    if not getattr(obj, "prechecked_at", None):
        return None
    by = obj.prechecked_by
    return {
        "by": (by.full_name or by.email) if by else "—",
        "at": obj.prechecked_at,
        "note": obj.precheck_note,
    }


class _Staff(APIView):
    permission_classes = [IsStaff]


class ControlMeView(_Staff):
    """Joriy ishchining roli — frontend menyu va tugmalarni shunga moslaydi."""

    @extend_schema(responses={200: dict})
    def get(self, request):
        role = staff_role(request.user)
        return Response(
            {
                "role": role,
                "role_title": AREA_TITLE.get(role, role),
                "kinds": list(visible_kinds(request.user)),
            }
        )


class ControlDashboardView(_Staff):
    """Bosh sahifa: o'z sohasidagi navbat; asosiy adminga — pul, ogohlantirishlar, platforma ham."""

    @extend_schema(responses={200: dict})
    def get(self, request):
        role = staff_role(request.user)
        queue = []
        for name, k in visible_kinds(request.user).items():
            state = actionable_state(k, role)
            qs = k.queryset().filter(**k.states[state])
            n = qs.count()
            oldest = (
                qs.order_by(k.waiting_field).values_list(k.waiting_field, flat=True).first() if n else None
            )
            age, overdue = dashboard._age(oldest)
            # adminga: moderatorda turganlar soni (ma'lumot uchun)
            waiting_other = (
                k.queryset().filter(**k.states["precheck"]).count() if k.two_stage and role == "admin" else 0
            )
            queue.append(
                {
                    "kind": name,
                    "title": k.title,
                    "icon": k.icon,
                    "count": n,
                    "oldest": age,
                    "overdue": overdue,
                    "state": state,
                    "with_moderator": waiting_other,
                }
            )
        logs = LogEntry.objects.select_related("user").order_by("-action_time")
        if role != "admin":
            logs = logs.filter(user=request.user)
        actions = [
            {
                "user": e.user.full_name or e.user.email,
                "object": e.object_repr,
                "message": e.get_change_message() or "o'zgartirildi",
                "at": e.action_time,
            }
            for e in logs[:15]
        ]
        data = {
            "role": role,
            "role_title": AREA_TITLE.get(role, role),
            "queue": queue,
            "queue_total": sum(q["count"] for q in queue),
            "recent_actions": actions,
            "money": None,
            "alerts": [],
            "platform": [],
        }
        if role == "admin":
            money = dashboard.money()
            money["chart"] = [{"day": d["day"], "value": d["value"], "pct": d["pct"]} for d in money["chart"]]
            data["money"] = money
            data["alerts"] = [{"text": a["text"]} for a in dashboard.alerts()]
            data["platform"] = [{"label": p["label"], "value": p["value"]} for p in dashboard.platform()]
        return Response(data)


class ControlListView(_Staff):
    """`?state=precheck|pending|rejected|approved|suspended`, `?q=`. Standart — ish kutayotgan holat."""

    @extend_schema(responses={200: dict})
    def get(self, request, kind):
        role = staff_role(request.user)
        k = _visible_kind(request, kind)
        default = actionable_state(k, role)
        state = request.query_params.get("state") or default
        if state not in k.states:
            raise ValidationError({"state": f"Mumkin: {', '.join(k.states)}"})
        qs = k.queryset().filter(**k.states[state])
        qs = (
            qs.order_by(k.waiting_field)
            if state in ("precheck", "pending")
            else qs.order_by(f"-{k.waiting_field}")
        )
        rows = []
        for obj in qs[:200]:
            age, overdue = dashboard._age(getattr(obj, k.waiting_field))
            rows.append(
                {
                    "id": obj.pk,
                    **k.row(obj),
                    "status": k.status_of(obj),
                    "waiting": age,
                    "overdue": overdue and state in ("precheck", "pending"),
                }
            )
        q = (request.query_params.get("q") or "").strip().lower()
        if q:
            rows = [r for r in rows if q in r["title"].lower() or q in (r["subtitle"] or "").lower()]
        return Response(
            {
                "kind": kind,
                "title": k.title,
                "states": list(k.states),
                "state": state,
                "default_state": default,
                "two_stage": k.two_stage,
                "can_suspend": k.suspend is not None and role == "admin",
                # Hamkorlik arizalarini Excel'dan qo'shish — faqat asosiy admin
                "import_key": APPLICATION_IMPORTS.get(kind) if role == "admin" else None,
                "results": rows,
                "counts": {s: k.queryset().filter(**f).count() for s, f in k.states.items()},
            }
        )


class ControlItemView(_Staff):
    @extend_schema(responses={200: dict})
    def get(self, request, kind, pk):
        role = staff_role(request.user)
        k = _visible_kind(request, kind)
        obj = get_object_or_404(k.queryset(), pk=pk)
        history = [
            {"user": e.user.full_name or e.user.email, "message": e.get_change_message(), "at": e.action_time}
            for e in LogEntry.objects.filter(
                content_type__app_label=obj._meta.app_label,
                content_type__model=obj._meta.model_name,
                object_id=str(obj.pk),
            )
            .select_related("user")
            .order_by("-action_time")[:20]
        ]
        return Response(
            {
                "kind": kind,
                "title": k.title,
                "id": obj.pk,
                "name": k.row(obj)["title"],
                "state": k.status_of(obj),
                "two_stage": k.two_stage,
                "role": role,
                "actions": allowed_actions(kind, k, obj, role),
                "precheck": _precheck_info(obj) if k.two_stage else None,
                "public_url": k.public_url(obj),
                "can_suspend": k.suspend is not None and role == "admin",
                "data": k.detail(obj, request),
                "history": history,
            }
        )


class ControlActionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000, default="")


class ControlActionView(_Staff):
    """POST .../approve | precheck (moderator → admin) | return (izoh majburiy) | suspend | activate."""

    ACTIONS = {
        "approve": "✅ Tasdiqlandi",
        "precheck": "🟢 Moderator tekshirdi — adminga yuborildi",
        "return": "↩️ Qaytarildi",
        "suspend": "⛔ To'xtatildi",
        "activate": "▶️ Faollashtirildi",
    }

    @extend_schema(request=ControlActionSerializer, responses={200: dict})
    def post(self, request, kind, pk, action):
        from apps.agencies import services as agency_services
        from apps.notifications import services as notify

        role = staff_role(request.user)
        k = _visible_kind(request, kind)
        if action not in self.ACTIONS:
            raise Http404
        obj = get_object_or_404(k.queryset(), pk=pk)
        if action not in allowed_actions(kind, k, obj, role):
            raise PermissionDenied(
                "Bu amal sizga ruxsat etilmagan." if role != "admin" else "Bu holatda bu amal qo'llanmaydi."
            )
        ser = ControlActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = ser.validated_data["note"].strip()

        if action == "return" and kind not in REVIEW_KINDS and len(note) < 5:
            raise ValidationError(
                {"note": "Qayerda kamchilik borligini yozing (kamida 5 belgi) — bu hamkorga yuboriladi."}
            )

        if action == "precheck":
            obj.prechecked_by = request.user
            obj.prechecked_at = timezone.now()
            obj.precheck_note = note
            obj.save(update_fields=["prechecked_by", "prechecked_at", "precheck_note", "updated_at"])
            notify.precheck_done(k.title, k.row(obj)["title"], obj, request.user, note)
        elif kind == "application":
            if action == "approve":
                agency_services.approve_application(obj, request.user)
            elif action == "return":
                agency_services.reject_application(obj, request.user, note)
            else:
                raise ValidationError({"detail": "Bu amal arizaga qo'llanmaydi."})
        else:
            fn = {"approve": k.approve, "return": k.reject, "suspend": k.suspend, "activate": k.activate}[
                action
            ]
            if fn is None:
                raise ValidationError({"detail": "Bu amal bu bo'limga qo'llanmaydi."})
            if action == "return":
                fn(obj, note)
            else:
                fn(obj)
        _log(request, obj, f"{self.ACTIONS[action]}" + (f": {note}" if note else ""))
        obj.refresh_from_db()
        return Response({"state": k.status_of(obj)}, status=status.HTTP_200_OK)


class ControlCertificateView(_Staff):
    """Gid sertifikati (yopiq fayl) — asosiy admin va gidlar moderatori."""

    def get(self, request, pk):
        from apps.guides.models import GuideProfile

        _visible_kind(request, "guide")
        g = get_object_or_404(GuideProfile, pk=pk)
        if not g.certificate_file:
            raise Http404
        return FileResponse(
            g.certificate_file.open("rb"), filename=g.certificate_file.name.rsplit("/", 1)[-1]
        )
