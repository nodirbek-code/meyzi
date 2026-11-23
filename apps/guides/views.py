from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from . import services
from .models import GuideBooking, GuideMeetingPoint, GuideProfile, GuideReview, GuideUnavailableDate
from .serializers import (
    CabinetGuideBookingSerializer,
    GuideBookingCreateSerializer,
    GuideBookingSerializer,
    GuideCardSerializer,
    GuideDetailSerializer,
    GuideReasonSerializer,
    GuideReviewCreateSerializer,
    GuideReviewSerializer,
    MeetingPointSerializer,
    MyGuideProfileSerializer,
    QuoteQuerySerializer,
    QuoteSerializer,
    UnavailableDateSerializer,
)


class IsApprovedGuide(BasePermission):
    message = "Bu bo'lim faqat tasdiqlangan gidlar uchun."

    def has_permission(self, request, view):
        profile = getattr(request.user, "guide_profile", None) if request.user.is_authenticated else None
        request.guide = profile
        return bool(profile and profile.is_approved)


# ---------- Ommaviy ----------


class GuideViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tasdiqlangan gidlar. Filtr: ?destination=samarqand&language=en&specialization=history&max_price=500000
    &date=2026-12-05 (shu kuni bo'sh). Saralash: ?ordering=-rating | price_full_day_uzs
    """

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    search_fields = ["display_name", "bio"]
    ordering_fields = ["rating", "price_full_day_uzs", "experience_years"]

    def get_queryset(self):
        qs = GuideProfile.objects.filter(status=GuideProfile.Status.APPROVED).prefetch_related(
            "destinations", "meeting_points"
        )
        p = self.request.query_params
        if v := p.get("destination"):
            qs = qs.filter(destinations__slug=v)
        if v := p.get("language"):
            qs = (
                qs.filter(languages__contains=[v])
                if _json_contains_supported()
                else _filter_list(qs, "languages", v)
            )
        if v := p.get("specialization"):
            qs = (
                qs.filter(specializations__contains=[v])
                if _json_contains_supported()
                else _filter_list(qs, "specializations", v)
            )
        if v := p.get("max_price"):
            qs = qs.filter(price_full_day_uzs__lte=int(v)) if v.isdigit() else qs
        if v := p.get("date"):
            try:
                day = timezone.datetime.fromisoformat(v).date()
            except ValueError:
                day = None
            if day:
                busy = Q(unavailable_dates__date=day) | Q(
                    bookings__status__in=GuideBooking.ACTIVE_STATUSES, bookings__start_date=day
                )
                qs = qs.exclude(pk__in=GuideProfile.objects.filter(busy).values("pk"))
                qs = qs.exclude(pk__in=_multi_day_busy(day))
        return qs.distinct().order_by("-rating", "display_name")

    def get_serializer_class(self):
        return GuideDetailSerializer if self.action == "retrieve" else GuideCardSerializer

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["get"], url_path="busy-dates")
    def busy_dates(self, request, slug=None):
        """Keyingi 90 kundagi band kunlar (kalendar uchun)."""
        guide = self.get_object()
        today = timezone.localdate()
        dates = services.busy_dates(guide, start=today, end=today + timedelta(days=90))
        return Response({"busy_dates": sorted(d.isoformat() for d in dates)})

    @extend_schema(parameters=[QuoteQuerySerializer], responses=QuoteSerializer)
    @action(detail=True, methods=["get"])
    def quote(self, request, slug=None):
        """Narx hisoblash: ?duration=full_day&days=1&group_size=6"""
        q = QuoteQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        data = services.quote(self.get_object(), **q.validated_data)
        return Response(QuoteSerializer(data).data)

    @extend_schema(responses=GuideReviewSerializer(many=True))
    @action(detail=True, methods=["get"])
    def reviews(self, request, slug=None):
        guide = self.get_object()
        qs = GuideReview.objects.filter(guide=guide, is_published=True).select_related("user")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(GuideReviewSerializer(page, many=True).data)


def _json_contains_supported() -> bool:
    from django.db import connection

    return connection.vendor == "postgresql"


def _filter_list(qs, field, value):
    """SQLite uchun (testlar): JSON ro'yxat ichida qidirish Python'da."""
    ids = [g.pk for g in qs if value in (getattr(g, field) or [])]
    return qs.filter(pk__in=ids)


def _multi_day_busy(day):
    """Ko'p kunlik bronlar bilan band gidlar."""
    ids = []
    for b in GuideBooking.objects.filter(
        status__in=GuideBooking.ACTIVE_STATUSES,
        days__gt=1,
        start_date__lt=day,
        start_date__gte=day - timedelta(days=14),
    ).only("guide_id", "start_date", "days"):
        if b.start_date <= day <= b.end_date:
            ids.append(b.guide_id)
    return ids


# ---------- Gid o'z profili ----------


class MyGuideProfileView(generics.GenericAPIView):
    """
    GET — profilim; POST — gid bo'lish arizasi (profil yaratiladi, holat `pending`);
    PATCH — tahrirlash (rad etilgan bo'lsa — qayta tekshiruvga yuboriladi).
    """

    serializer_class = MyGuideProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _profile(self):
        profile = GuideProfile.objects.filter(user=self.request.user).first()
        if not profile:
            raise NotFound("Gid profili yo'q. POST bilan ariza yuboring.")
        return profile

    def get(self, request):
        return Response(self.get_serializer(self._profile()).data)

    def post(self, request):
        if GuideProfile.objects.filter(user=request.user).exists():
            return Response({"detail": "Profil allaqachon bor — PATCH bilan tahrirlang."}, status=400)
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        profile = ser.save(
            user=request.user, slug=services.unique_guide_slug(ser.validated_data["display_name"])
        )
        services.submit_profile(profile, is_new=True)
        return Response(self.get_serializer(profile).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = self._profile()
        ser = self.get_serializer(profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        profile = ser.save()
        services.submit_profile(profile, is_new=False, details="profil tahrirlandi")
        return Response(self.get_serializer(profile).data)


# ---------- Turist: gid bronlari ----------


class GuideBookingViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Gidni bron qilish (so'rov). Gid 24 soatda javob beradi; qabul qilgach — to'lov."""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "code"
    filterset_fields = ["status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GuideBooking.objects.none()
        return GuideBooking.objects.filter(user=self.request.user).select_related(
            "guide", "destination", "review"
        )

    def get_serializer_class(self):
        return GuideBookingCreateSerializer if self.action == "create" else GuideBookingSerializer

    @extend_schema(request=GuideBookingCreateSerializer, responses={201: GuideBookingSerializer})
    def create(self, request, *args, **kwargs):
        ser = GuideBookingCreateSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        booking = services.request_booking(user=request.user, **ser.validated_data)
        return Response(GuideBookingSerializer(booking).data, status=201)

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["get"], url_path="cancel-preview")
    def cancel_preview(self, request, code=None):
        booking = self.get_object()
        can = booking.status in GuideBooking.ACTIVE_STATUSES and booking.starts_at > timezone.now()
        refund = services.refund_preview(booking, by=GuideBooking.CancelledBy.TOURIST) if can else 0
        return Response({"can_cancel": can, "refund_uzs": refund})

    @extend_schema(request=GuideReasonSerializer, responses=GuideBookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, code=None):
        ser = GuideReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = services.cancel(
            self.get_object(), by=GuideBooking.CancelledBy.TOURIST, reason=ser.validated_data["reason"]
        )
        return Response(GuideBookingSerializer(booking).data)

    @extend_schema(request=GuideReviewCreateSerializer, responses={201: GuideReviewSerializer})
    @action(detail=True, methods=["post"])
    def review(self, request, code=None):
        ser = GuideReviewCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        review = services.create_review(user=request.user, booking=self.get_object(), **ser.validated_data)
        return Response(GuideReviewSerializer(review).data, status=201)


# ---------- Gid kabineti ----------


class CabinetGuideBookingViewSet(viewsets.ReadOnlyModelViewSet):
    """Gidga kelgan bronlar: qabul qilish, rad etish, bekor qilish, "turist kelmadi"."""

    serializer_class = CabinetGuideBookingSerializer
    permission_classes = [IsApprovedGuide]
    lookup_field = "code"
    filterset_fields = ["status"]

    def get_permissions(self):
        # Bekor qilish/kelmadi — profil to'xtatilgan bo'lsa ham (mavjud bronlarni yopish uchun)
        if self.action in ("list", "retrieve", "cancel", "tourist_no_show"):
            return [_HasGuideProfile()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GuideBooking.objects.none()
        return GuideBooking.objects.filter(guide=self.request.guide).select_related(
            "guide", "destination", "review"
        )

    @extend_schema(request=None, responses=CabinetGuideBookingSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, code=None):
        return Response(self.get_serializer(services.accept(self.get_object())).data)

    @extend_schema(request=GuideReasonSerializer, responses=CabinetGuideBookingSerializer)
    @action(detail=True, methods=["post"])
    def decline(self, request, code=None):
        ser = GuideReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return Response(self.get_serializer(services.decline(self.get_object(), **ser.validated_data)).data)

    @extend_schema(request=GuideReasonSerializer, responses=CabinetGuideBookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, code=None):
        """Gid bekor qiladi: turistga 100%, gidga jarima (vaqtga qarab)."""
        ser = GuideReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = services.cancel(
            self.get_object(), by=GuideBooking.CancelledBy.GUIDE, reason=ser.validated_data["reason"]
        )
        return Response(self.get_serializer(booking).data)

    @extend_schema(request=None, responses=CabinetGuideBookingSerializer)
    @action(detail=True, methods=["post"], url_path="tourist-no-show")
    def tourist_no_show(self, request, code=None):
        """Turist kelmadi (boshlanishdan 1 soat o'tgach): gidga 30% kompensatsiya."""
        return Response(self.get_serializer(services.report_tourist_no_show(self.get_object())).data)


class _HasGuideProfile(BasePermission):
    message = "Gid profili yo'q."

    def has_permission(self, request, view):
        profile = getattr(request.user, "guide_profile", None) if request.user.is_authenticated else None
        request.guide = profile
        return profile is not None


class CabinetGuideTourBookingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Gid professional gid sifatida tanlangan turlar (kelgusi, faol bronlar). Faqat o'qish."""

    permission_classes = [_HasGuideProfile]
    pagination_class = None

    def get_serializer_class(self):
        from .serializers import GuideTourBookingSerializer

        return GuideTourBookingSerializer

    def get_queryset(self):
        from django.db.models import Q

        from apps.bookings.models import Booking

        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return (
            Booking.objects.filter(guide=self.request.guide, departure__date__gte=timezone.localdate())
            .filter(
                Q(status=Booking.Status.CONFIRMED)
                | Q(status=Booking.Status.PENDING_PAYMENT, expires_at__gt=timezone.now())
            )
            .select_related("tour", "departure", "agency")
            .order_by("departure__date")
        )


class CabinetUnavailableDateViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """Gid ishlamaydigan kunlarini belgilaydi."""

    serializer_class = UnavailableDateSerializer
    permission_classes = [_HasGuideProfile]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GuideUnavailableDate.objects.none()
        return GuideUnavailableDate.objects.filter(guide=self.request.guide, date__gte=timezone.localdate())

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError

        day = serializer.validated_data["date"]
        if GuideUnavailableDate.objects.filter(guide=self.request.guide, date=day).exists():
            raise ValidationError({"date": "Bu kun allaqachon belgilangan."})
        if services.busy_dates(self.request.guide, start=day, end=day):
            raise ValidationError({"date": "Bu kunda bron bor — avval uni hal qiling."})
        serializer.save(guide=self.request.guide)


class CabinetMeetingPointViewSet(viewsets.ModelViewSet):
    """Gidning uchrashuv joylari. Turist bron qilganda faqat shulardan (faol) birini tanlaydi.

    Bronlarda ishlatilgan joy o'chirilmaydi — nofaol qilinadi (eski bronlarda nusxasi saqlanadi).
    """

    serializer_class = MeetingPointSerializer
    permission_classes = [_HasGuideProfile]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GuideMeetingPoint.objects.none()
        return GuideMeetingPoint.objects.filter(guide=self.request.guide).select_related("destination")

    def perform_create(self, serializer):
        point = serializer.save(guide=self.request.guide)
        services.submit_profile(
            self.request.guide, is_new=False, details=f"yangi uchrashuv joyi: {point.name}"
        )

    def perform_update(self, serializer):
        point = serializer.save()
        services.submit_profile(
            self.request.guide, is_new=False, details=f"uchrashuv joyi o'zgardi: {point.name}"
        )

    def perform_destroy(self, point):
        if point.bookings.exists():
            point.is_active = False
            point.save(update_fields=["is_active", "updated_at"])
        else:
            point.delete()


class CabinetGuideReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Gid o'z sharhlarini ko'radi (tekshiruvdagilari ham) va javob yozadi."""

    serializer_class = GuideReviewSerializer
    permission_classes = [_HasGuideProfile]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GuideReview.objects.none()
        return GuideReview.objects.filter(guide=self.request.guide).select_related("user")

    @extend_schema(request=GuideReasonSerializer, responses=GuideReviewSerializer)
    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        text = str(request.data.get("text", ""))[:2000]
        review = self.get_object()
        review.guide_reply = text
        review.save(update_fields=["guide_reply", "updated_at"])
        return Response(self.get_serializer(review).data)
