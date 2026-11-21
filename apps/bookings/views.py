from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.agencies.permissions import IsAgencyMember
from apps.tours.policies import POLICY_TEXT

from . import services
from .models import Booking
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    CabinetBookingSerializer,
    CancelPreviewSerializer,
    CancelSerializer,
)


class _BookingQuerysetMixin:
    lookup_field = "code"
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "departure_at"]

    def base_queryset(self):
        return Booking.objects.select_related(
            "tour", "agency", "departure", "user", "review"
        ).prefetch_related("travelers", "tour__media")

    def get_object(self):
        return services.refresh_if_expired(super().get_object())

    def list(self, request, *args, **kwargs):
        services.expire_due_bookings()  # ro'yxatda eskirgan "to'lov kutilmoqda" ko'rinmasin
        return super().list(request, *args, **kwargs)


class BookingViewSet(_BookingQuerysetMixin, mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """
    Turistning bronlari.
    POST — bron qilish: joylar 30 daqiqaga band qilinadi (`expires_at`), shu vaqtda to'lash kerak.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return self.base_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        return BookingCreateSerializer if self.action == "create" else BookingSerializer

    @extend_schema(request=BookingCreateSerializer, responses={201: BookingSerializer})
    def create(self, request, *args, **kwargs):
        ser = BookingCreateSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        booking = services.create_booking(
            user=request.user,
            departure_id=data["departure"],
            seats=data["seats"],
            contact_name=data["contact_name"],
            contact_phone=data["contact_phone"],
            contact_email=data["contact_email"],
            note=data["note"],
            travelers=data["travelers"],
        )
        booking = self.base_queryset().get(pk=booking.pk)
        return Response(BookingSerializer(booking, context=self.get_serializer_context()).data, status=201)

    @extend_schema(responses=CancelPreviewSerializer)
    @action(detail=True, methods=["get"], url_path="cancel-preview")
    def cancel_preview(self, request, code=None):
        """Hozir bekor qilsam, qancha qaytariladi?"""
        booking = self.get_object()
        can_cancel = booking.holds_seats and booking.departure_at > timezone.now()
        return Response(
            {
                "can_cancel": can_cancel,
                "refund_uzs": services.refund_preview(booking, by=Booking.CancelledBy.TOURIST)
                if can_cancel
                else 0,
                "cancellation_policy": booking.cancellation_policy,
                "policy_text": POLICY_TEXT[booking.cancellation_policy],
            }
        )

    @extend_schema(request=CancelSerializer, responses=BookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, code=None):
        ser = CancelSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = services.cancel_booking(
            self.get_object(), by=Booking.CancelledBy.TOURIST, reason=ser.validated_data["reason"]
        )
        booking = self.base_queryset().get(pk=booking.pk)
        return Response(BookingSerializer(booking, context=self.get_serializer_context()).data)


class CabinetBookingViewSet(_BookingQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """Agentlik bronlari. Filtr: ?status=confirmed&tour=<slug>&departure=<id>"""

    serializer_class = CabinetBookingSerializer
    permission_classes = [IsAgencyMember]
    search_fields = ["code", "contact_name", "contact_phone"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        qs = self.base_queryset().filter(agency=self.request.agency)
        if tour := self.request.query_params.get("tour"):
            qs = qs.filter(tour__slug=tour)
        if departure := self.request.query_params.get("departure"):
            qs = qs.filter(departure_id=departure)
        return qs

    @extend_schema(request=CancelSerializer, responses=CabinetBookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, code=None):
        """Agentlik bronni bekor qiladi — turistga 100% qaytariladi."""
        ser = CancelSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = services.cancel_booking(
            self.get_object(), by=Booking.CancelledBy.AGENCY, reason=ser.validated_data["reason"]
        )
        booking = self.base_queryset().get(pk=booking.pk)
        return Response(self.get_serializer(booking).data, status=status.HTTP_200_OK)
