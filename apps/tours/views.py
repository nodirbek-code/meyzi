from datetime import timedelta

from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.agencies.models import Agency
from apps.agencies.permissions import IsAgencyMember
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel
from apps.notifications import services as notify

from .filters import TourFilter
from .models import Departure, ItineraryDay, Tour, TourCategory, TourMedia
from .serializers import (
    CabinetDepartureSerializer,
    CabinetMediaSerializer,
    CabinetTourSerializer,
    TourCardSerializer,
    TourCategorySerializer,
    TourDetailSerializer,
    TourGuideOptionSerializer,
)


def upcoming_departures_prefetch():
    return Prefetch(
        "departures",
        queryset=Departure.objects.filter(
            status=Departure.Status.OPEN, date__gte=timezone.localdate()
        ).order_by("date"),
        to_attr="upcoming_departures",
    )


def public_tours():
    return Tour.objects.filter(
        status=Tour.Status.PUBLISHED,
        agency__status=Agency.Status.ACTIVE,
        agency__moderation_status=Agency.Moderation.APPROVED,
        destination__is_published=True,
    )


# ---------- Ommaviy API ----------


class TourCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TourCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        published = Q(tours__in=public_tours())
        return (
            TourCategory.objects.filter(is_active=True)
            .annotate(tours_count=Count("tours", filter=published, distinct=True))
            .order_by("sort_order", "name")
        )


class TourViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Turlar katalogi.
    Filtrlar: destination, category (vergul bilan), agency, min_price, max_price, min_days, max_days,
    date, date_from, date_to, cancellation_policy, is_featured, search.
    Saralash: ordering=price_uzs | -price_uzs | duration_days | -rating | -published_at
    """

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    filterset_class = TourFilter
    search_fields = ["title", "short_description", "destination__name", "agency__name"]
    ordering_fields = ["price_uzs", "duration_days", "rating", "published_at"]

    def get_queryset(self):
        qs = (
            public_tours()
            .select_related("destination", "agency")
            .prefetch_related("categories", "media", upcoming_departures_prefetch())
            .order_by("-is_featured", "-published_at")
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "places",
                Prefetch("itinerary", queryset=ItineraryDay.objects.prefetch_related("items")),
                Prefetch("guides", queryset=GuideProfile.objects.filter(status=GuideProfile.Status.APPROVED)),
                Prefetch(
                    "hotels",
                    queryset=Hotel.objects.filter(
                        status=Hotel.Status.APPROVED, destination__is_published=True
                    )
                    .select_related("destination")
                    .prefetch_related("images"),
                ),
            )
        return qs

    def get_serializer_class(self):
        return TourDetailSerializer if self.action == "retrieve" else TourCardSerializer

    @extend_schema(
        parameters=[OpenApiParameter("departure", int, required=True, description="Jo'nash sanasi ID")],
        responses=TourGuideOptionSerializer(many=True),
    )
    @action(detail=True, methods=["get"])
    def guides(self, request, slug=None):
        """Ixtiyoriy professional gid: shu sana uchun turga biriktirilgan gidlar va ularning bo'shligi."""
        from apps.bookings.services import guide_options

        tour = self.get_object()
        try:
            departure = tour.departures.get(pk=int(request.query_params.get("departure", "")))
        except (ValueError, Departure.DoesNotExist):
            raise ValidationError({"departure": "Jo'nash sanasini tanlang."}) from None
        options = guide_options(departure)
        return Response(TourGuideOptionSerializer(options, many=True, context={"request": request}).data)

    @extend_schema(responses={200: dict})
    @action(detail=False, methods=["get"])
    def calendar(self, request):
        """Sana tasmasi uchun: keyingi `days` (≤ 90) kundagi bo'sh joyli jo'nashlar soni.
        Katalog filtrlari (destination, category...) ham qo'llanadi. Javob: [{"date", "tours"}]."""
        try:
            days = max(1, min(90, int(request.query_params.get("days", 45))))
        except ValueError:
            days = 45
        today = timezone.localdate()
        tours = self.filter_queryset(self.get_queryset()).values("pk")
        rows = (
            Departure.objects.filter(
                tour__in=tours,
                status=Departure.Status.OPEN,
                seats_booked__lt=F("seats_total"),
                date__gte=today,
                date__lte=today + timedelta(days=days - 1),
            )
            .values("date")
            .annotate(tours=Count("tour", distinct=True))
            .order_by("date")
        )
        return Response([{"date": r["date"].isoformat(), "tours": r["tours"]} for r in rows])


# ---------- Agentlik kabineti ----------


class CabinetTourViewSet(viewsets.ModelViewSet):
    """Agentlik o'z turlarini boshqaradi. Yangi tur — qoralama; `submit` bilan e'longa yuboriladi."""

    serializer_class = CabinetTourSerializer
    permission_classes = [IsAgencyMember]
    lookup_field = "slug"
    filterset_fields = ["status"]
    search_fields = ["title"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Tour.objects.none()
        return (
            Tour.objects.filter(agency=self.request.agency)
            .select_related("destination")
            .prefetch_related("categories", "places", "media", "itinerary__items")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(agency=self.request.agency, status=Tour.Status.DRAFT)

    def perform_update(self, serializer):
        tour = serializer.save()
        resubmit_tour(tour, "tur tahrirlandi")

    def perform_destroy(self, tour):
        if tour.bookings.exists():
            raise ValidationError({"detail": "Bronlari bor turni o'chirib bo'lmaydi — arxivlang."})
        tour.delete()

    @extend_schema(request=None, responses=CabinetTourSerializer)
    @action(detail=True, methods=["post"])
    def submit(self, request, slug=None):
        """E'longa yuborish → admin tekshiruvi. Faqat platformaning o'z agentligi (auto_publish) — darhol."""
        tour = self.get_object()
        if tour.status not in (Tour.Status.DRAFT, Tour.Status.REJECTED, Tour.Status.ARCHIVED):
            raise ValidationError(
                {"detail": "Faqat qoralama, rad etilgan yoki arxivdagi turni yuborish mumkin."}
            )
        if not tour.media.exists():
            raise ValidationError({"detail": "Kamida bitta rasm yuklang."})
        # Uchrashuv joyi majburiy va aniq bo'lsin: nomi + xaritadagi joyi (havola yoki koordinata)
        if not tour.meeting_point.strip():
            raise ValidationError({"meeting_point": "Uchrashuv joyini kiriting."})
        has_coords = tour.meeting_latitude is not None and tour.meeting_longitude is not None
        if not (tour.meeting_map_url or has_coords):
            raise ValidationError(
                {"meeting_map_url": "Uchrashuv joyining xarita havolasini yoki koordinatasini kiriting."}
            )
        if request.agency.is_platform and request.agency.auto_publish:
            tour.publish()
        else:
            tour.status = Tour.Status.PENDING_REVIEW
        tour.moderation_note = ""
        tour.save()
        if tour.status == Tour.Status.PENDING_REVIEW:
            notify.tour_submitted(tour)
        return Response(self.get_serializer(tour).data)

    @extend_schema(request=None, responses=CabinetTourSerializer)
    @action(detail=True, methods=["post"])
    def archive(self, request, slug=None):
        tour = self.get_object()
        tour.status = Tour.Status.ARCHIVED
        tour.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(tour).data)


def resubmit_tour(tour: Tour, details: str = "") -> Tour:
    """E'lon qilingan turni agentlik o'zgartirdi — qayta tekshiruvga (tasdiqlanguncha saytda ko'rinmaydi)."""
    agency = tour.agency
    if tour.status == Tour.Status.PUBLISHED and not (agency.is_platform and agency.auto_publish):
        tour.status = Tour.Status.PENDING_REVIEW
        tour.moderation_note = ""
        tour.save(update_fields=["status", "moderation_note", "updated_at"])
        notify.changes_submitted("Tur", tour.title, tour, details)
    return tour


def reject_tour(tour: Tour, note: str) -> Tour:
    """Admin qaytaradi: izoh agentlikka yuboriladi, u tuzatib qayta yuboradi."""
    from apps.notifications import user_events

    tour.status = Tour.Status.REJECTED
    tour.moderation_note = note
    tour.save(update_fields=["status", "moderation_note", "updated_at"])
    user_events.tour_moderated(tour)
    return tour


class _TourChildMixin:
    """`/cabinet/tours/{tour_slug}/...` — tur agentlikka tegishli ekanini tekshiradi."""

    permission_classes = [IsAgencyMember]

    def get_tour(self):
        if not hasattr(self, "_tour"):
            self._tour = get_object_or_404(Tour, slug=self.kwargs["tour_slug"], agency=self.request.agency)
        return self._tour

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if "tour_slug" in self.kwargs and getattr(self.request, "agency", None):
            ctx["tour"] = self.get_tour()
        return ctx


class CabinetDepartureViewSet(_TourChildMixin, viewsets.ModelViewSet):
    serializer_class = CabinetDepartureSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Departure.objects.none()
        return self.get_tour().departures.order_by("date")

    def perform_create(self, serializer):
        serializer.save(tour=self.get_tour())

    def perform_update(self, serializer):
        from apps.bookings.services import cancel_departure

        was_cancelled = serializer.instance.status == Departure.Status.CANCELLED
        departure = serializer.save()
        if departure.status == Departure.Status.CANCELLED and not was_cancelled:
            cancel_departure(departure)  # barcha bronlar 100% qaytarish bilan bekor

    def perform_destroy(self, departure):
        if departure.bookings.exists():
            raise ValidationError(
                {"detail": "Bron qilingan sanani o'chirib bo'lmaydi — holatini 'cancelled' qiling."}
            )
        departure.delete()


class CabinetMediaViewSet(
    _TourChildMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CabinetMediaSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TourMedia.objects.none()
        return self.get_tour().media.all()

    def perform_create(self, serializer):
        self._save(serializer, tour=self.get_tour())
        resubmit_tour(self.get_tour(), "yangi rasm/video yuklandi")

    def perform_update(self, serializer):
        self._save(serializer)
        resubmit_tour(self.get_tour(), "rasm/video o'zgardi")

    def perform_destroy(self, media):
        media.delete()
        resubmit_tour(self.get_tour(), "rasm/video o'chirildi")

    def _save(self, serializer, **extra):
        media = serializer.save(**extra)
        if media.is_cover:
            TourMedia.objects.filter(tour=media.tour, is_cover=True).exclude(pk=media.pk).update(
                is_cover=False
            )


class CabinetStatsView(viewsets.ViewSet):
    """Kabinet bosh sahifasi uchun qisqa statistika."""

    permission_classes = [IsAgencyMember]

    @extend_schema(responses={200: dict})
    def list(self, request):
        tours = Tour.objects.filter(agency=request.agency)
        upcoming = Departure.objects.filter(
            tour__agency=request.agency, date__gte=timezone.localdate(), status=Departure.Status.OPEN
        )
        by_status = dict(tours.values_list("status").annotate(n=Count("id")))
        return Response(
            {
                "tours_total": tours.count(),
                "tours_by_status": {s: by_status.get(s, 0) for s in Tour.Status.values},
                "upcoming_departures": upcoming.count(),
                "upcoming_seats_total": sum(upcoming.values_list("seats_total", flat=True)),
                "upcoming_seats_booked": sum(upcoming.values_list("seats_booked", flat=True)),
                "sold_out_departures": upcoming.filter(seats_booked__gte=F("seats_total")).count(),
            },
            status=status.HTTP_200_OK,
        )
