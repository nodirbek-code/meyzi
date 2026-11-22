from django.conf import settings
from django.db import connection
from django.db.models import Min, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from . import services
from .models import Hotel, HotelBooking, HotelImage, HotelMember, HotelReview, RoomType
from .serializers import (
    AvailabilityQuerySerializer,
    CabinetHotelBookingSerializer,
    HotelBookingCreateSerializer,
    HotelBookingSerializer,
    HotelCardSerializer,
    HotelDetailSerializer,
    HotelImageSerializer,
    HotelReasonSerializer,
    HotelReviewCreateSerializer,
    HotelReviewSerializer,
    MyHotelSerializer,
    ReplySerializer,
    RoomOfferSerializer,
    RoomTypeSerializer,
)


class IsHotelMember(BasePermission):
    message = "Bu bo'lim faqat mehmonxona xodimlari uchun."

    def has_permission(self, request, view):
        membership = (
            HotelMember.objects.select_related("hotel").filter(user=request.user).first()
            if request.user.is_authenticated
            else None
        )
        request.hotel = membership.hotel if membership else None
        return bool(membership and membership.hotel.status != Hotel.Status.SUSPENDED)


def _offers(room_types, request, q) -> list[dict]:
    room_types = list(room_types)
    free = services.availability(room_types, q["check_in"], q["check_out"]) if q.get("check_in") else {}
    nights = q.get("nights")
    out = []
    for rt in room_types:
        out.append(
            {
                **RoomTypeSerializer(rt, context={"request": request}).data,
                "available_rooms": free.get(rt.pk) if nights else None,
                "nights": nights,
                "stay_total_uzs": rt.price_per_night_uzs * nights if nights else None,
            }
        )
    return out


# ---------- Ommaviy ----------


class HotelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Mehmonxonalar. Filtr: ?destination=samarqand&stars=4&kind=hotel&amenity=wifi&max_price=800000
    Sanalar bilan (faqat bo'sh xonasi borlar): ?check_in=2026-12-10&check_out=2026-12-12&guests=2&rooms=1
    """

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    search_fields = ["name", "address", "description"]
    ordering_fields = ["rating", "min_price_uzs", "stars"]

    def _query(self):
        q = AvailabilityQuerySerializer(data=self.request.query_params)
        q.is_valid(raise_exception=True)
        return q.validated_data

    def get_queryset(self):
        qs = (
            Hotel.objects.filter(status=Hotel.Status.APPROVED, destination__is_published=True)
            .select_related("destination")
            .prefetch_related("images")
            .annotate(
                min_price_uzs=Min("room_types__price_per_night_uzs", filter=Q(room_types__is_active=True))
            )
        )
        p = self.request.query_params
        if v := p.get("destination"):
            qs = qs.filter(destination__slug=v)
        if v := p.get("stars"):
            qs = qs.filter(stars__gte=int(v)) if v.isdigit() else qs
        if v := p.get("kind"):
            qs = qs.filter(kind=v)
        if (v := p.get("max_price")) and v.isdigit():
            qs = qs.filter(min_price_uzs__lte=int(v))
        if v := p.get("amenity"):
            if connection.vendor == "postgresql":
                qs = qs.filter(amenities__contains=[v])
            else:
                qs = qs.filter(pk__in=[h.pk for h in qs if v in (h.amenities or [])])
        if self.action == "list":
            q = self._query()
            if q.get("check_in"):
                qs = qs.filter(pk__in=self._available_hotel_ids(qs, q))
        return qs.order_by("-is_featured", "-rating", "name")

    @staticmethod
    def _available_hotel_ids(qs, q):
        """Kamida bitta xona turida kerakli xonalar bo'sh va sig'im yetarli."""
        per_room = -(-q["guests"] // q["rooms"])  # yuqoriga yaxlitlash
        room_types = RoomType.objects.filter(hotel__in=qs, is_active=True, capacity__gte=per_room)
        free = services.availability(room_types, q["check_in"], q["check_out"])
        return {rt.hotel_id for rt in room_types if free[rt.pk] >= q["rooms"]}

    def get_serializer_class(self):
        return HotelDetailSerializer if self.action == "retrieve" else HotelCardSerializer

    @extend_schema(parameters=[AvailabilityQuerySerializer], responses=RoomOfferSerializer(many=True))
    @action(detail=True, methods=["get"])
    def rooms(self, request, slug=None):
        """Xona turlari. Sanalar berilsa — har biri uchun bo'sh xonalar va butun muddat narxi."""
        hotel = self.get_object()
        q = self._query()
        return Response(_offers(hotel.room_types.filter(is_active=True), request, q))

    @extend_schema(responses=HotelReviewSerializer(many=True))
    @action(detail=True, methods=["get"])
    def reviews(self, request, slug=None):
        qs = HotelReview.objects.filter(hotel=self.get_object(), is_published=True).select_related("user")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(HotelReviewSerializer(page, many=True).data)


# ---------- Mehmonxona egasi: ariza / profil ----------


class MyHotelView(generics.GenericAPIView):
    """GET — mehmonxonam; POST — ro'yxatdan o'tkazish arizasi (pending); PATCH — tahrirlash."""

    serializer_class = MyHotelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _hotel(self):
        m = HotelMember.objects.select_related("hotel").filter(user=self.request.user).first()
        if not m:
            raise NotFound("Mehmonxona yo'q. POST bilan ariza yuboring.")
        return m.hotel

    def get(self, request):
        return Response(self.get_serializer(self._hotel()).data)

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        hotel = services.register_hotel(user=request.user, **ser.validated_data)
        return Response(self.get_serializer(hotel).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        hotel = self._hotel()
        if hotel.status == Hotel.Status.SUSPENDED:
            raise ValidationError(
                {"detail": f"Mehmonxona to'xtatilgan. {settings.BRAND_NAME} bilan bog'laning."}
            )
        ser = self.get_serializer(hotel, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        hotel = ser.save()
        if hotel.status == Hotel.Status.REJECTED:
            hotel.status = Hotel.Status.PENDING
            hotel.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(hotel).data)


# ---------- Turist: bronlar ----------


class HotelBookingViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Mehmonxona broni: xonalar 30 daqiqaga band qilinadi (`expires_at`)."""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "code"
    filterset_fields = ["status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return HotelBooking.objects.none()
        return HotelBooking.objects.filter(user=self.request.user).select_related(
            "hotel", "room_type", "review"
        )

    def get_object(self):
        return services.refresh_if_expired(super().get_object())

    def list(self, request, *args, **kwargs):
        services.expire_due()
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        return HotelBookingCreateSerializer if self.action == "create" else HotelBookingSerializer

    @extend_schema(request=HotelBookingCreateSerializer, responses={201: HotelBookingSerializer})
    def create(self, request, *args, **kwargs):
        ser = HotelBookingCreateSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        d = dict(ser.validated_data)
        booking = services.create_booking(user=request.user, room_type_id=d.pop("room_type"), **d)
        return Response(HotelBookingSerializer(booking).data, status=201)

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["get"], url_path="cancel-preview")
    def cancel_preview(self, request, code=None):
        b = self.get_object()
        can = b.status in HotelBooking.ACTIVE_STATUSES and b.check_in_at > timezone.now()
        refund = services.refund_preview(b, by=HotelBooking.CancelledBy.TOURIST) if can else 0
        return Response({"can_cancel": can, "refund_uzs": refund})

    @extend_schema(request=HotelReasonSerializer, responses=HotelBookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, code=None):
        ser = HotelReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        b = services.cancel(self.get_object(), by=HotelBooking.CancelledBy.TOURIST, **ser.validated_data)
        return Response(HotelBookingSerializer(b).data)

    @extend_schema(request=HotelReviewCreateSerializer, responses={201: HotelReviewSerializer})
    @action(detail=True, methods=["post"])
    def review(self, request, code=None):
        ser = HotelReviewCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        review = services.create_review(user=request.user, booking=self.get_object(), **ser.validated_data)
        return Response(HotelReviewSerializer(review).data, status=201)


# ---------- Mehmonxona kabineti ----------


class CabinetRoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [IsHotelMember]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RoomType.objects.none()
        return RoomType.objects.filter(hotel=self.request.hotel)

    def perform_create(self, serializer):
        serializer.save(hotel=self.request.hotel)

    def perform_destroy(self, room_type):
        if room_type.bookings.exists():
            raise ValidationError({"detail": "Bronlari bor xona turini o'chirib bo'lmaydi — sotuvdan oling."})
        room_type.delete()


class CabinetHotelImageViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = HotelImageSerializer
    permission_classes = [IsHotelMember]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return HotelImage.objects.none()
        return HotelImage.objects.filter(hotel=self.request.hotel)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["hotel"] = getattr(self.request, "hotel", None)  # galereya chegarasi (20 rasm / 4 video) uchun
        return ctx

    def perform_create(self, serializer):
        image = serializer.save(hotel=self.request.hotel)
        if image.is_cover:
            HotelImage.objects.filter(hotel=image.hotel, is_cover=True).exclude(pk=image.pk).update(
                is_cover=False
            )


class CabinetHotelBookingViewSet(viewsets.ReadOnlyModelViewSet):
    """Mehmonxona bronlari. Filtr: ?status=confirmed&check_in=2026-12-10"""

    serializer_class = CabinetHotelBookingSerializer
    permission_classes = [IsHotelMember]
    lookup_field = "code"
    filterset_fields = ["status", "check_in", "room_type"]
    search_fields = ["code", "contact_name", "contact_phone"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return HotelBooking.objects.none()
        return HotelBooking.objects.filter(hotel=self.request.hotel).select_related(
            "hotel", "room_type", "review"
        )

    @extend_schema(request=HotelReasonSerializer, responses=CabinetHotelBookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, code=None):
        """Mehmonxona bekor qiladi — mehmonga 100% qaytariladi."""
        ser = HotelReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        b = services.cancel(self.get_object(), by=HotelBooking.CancelledBy.HOTEL, **ser.validated_data)
        return Response(self.get_serializer(b).data)


class CabinetHotelReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HotelReviewSerializer
    permission_classes = [IsHotelMember]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return HotelReview.objects.none()
        return HotelReview.objects.filter(hotel=self.request.hotel).select_related("user")

    @extend_schema(request=ReplySerializer, responses=HotelReviewSerializer)
    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        ser = ReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        review = self.get_object()
        review.hotel_reply = ser.validated_data["text"]
        review.save(update_fields=["hotel_reply", "updated_at"])
        return Response(self.get_serializer(review).data)
