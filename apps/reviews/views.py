from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.agencies.permissions import IsAgencyMember

from . import services
from .models import Review
from .serializers import (
    AgencyReplySerializer,
    MyReviewSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)

EDIT_WINDOW_DAYS = 14


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Ommaviy sharhlar. Filtr: ?tour=<slug>&agency=<slug>&rating=5"""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        qs = Review.objects.filter(status=Review.Status.PUBLISHED).select_related("user", "tour", "agency")
        params = self.request.query_params
        if tour := params.get("tour"):
            qs = qs.filter(tour__slug=tour)
        if agency := params.get("agency"):
            qs = qs.filter(agency__slug=agency)
        if rating := params.get("rating"):
            qs = qs.filter(rating=rating)
        return qs


class MyReviewViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """
    O'z sharhlarim. POST — yakunlangan bron uchun sharh: {"booking": "LZ...", "rating": 5, "text": "..."}.
    PATCH — 14 kun ichida tahrirlash.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return Review.objects.filter(user=self.request.user).select_related(
            "user", "tour", "agency", "booking"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        if self.action in ("update", "partial_update"):
            return ReviewUpdateSerializer
        return MyReviewSerializer

    @extend_schema(request=ReviewCreateSerializer, responses={201: MyReviewSerializer})
    def create(self, request, *args, **kwargs):
        ser = ReviewCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        review = services.create_review(
            user=request.user, booking_code=d["booking"], rating=d["rating"], text=d["text"]
        )
        return Response(MyReviewSerializer(review).data, status=201)

    @extend_schema(request=ReviewUpdateSerializer, responses=MyReviewSerializer)
    def partial_update(self, request, *args, **kwargs):
        review = self.get_object()
        if (timezone.now() - review.created_at).days >= EDIT_WINDOW_DAYS:
            raise ValidationError({"detail": f"Sharhni {EDIT_WINDOW_DAYS} kun ichida tahrirlash mumkin."})
        ser = ReviewUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        review = services.update_review(review, **ser.validated_data)
        return Response(MyReviewSerializer(review).data)


class CabinetReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Agentlik turlariga yozilgan sharhlar (yashirilganlari ham) va javob berish."""

    serializer_class = MyReviewSerializer
    permission_classes = [IsAgencyMember]
    filterset_fields = ["rating", "status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return Review.objects.filter(agency=self.request.agency).select_related(
            "user", "tour", "agency", "booking"
        )

    @extend_schema(request=AgencyReplySerializer, responses=MyReviewSerializer)
    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        """Sharhga javob (bo'sh matn — javobni o'chirish)."""
        ser = AgencyReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        review = services.agency_reply(self.get_object(), ser.validated_data["text"])
        return Response(self.get_serializer(review).data)
