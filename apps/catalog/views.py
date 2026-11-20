from django.db.models import Count, Q
from rest_framework import viewsets

from apps.core.permissions import IsAdminOrReadOnly

from .filters import PlaceFilter
from .models import Destination, Place
from .serializers import (
    DestinationDetailSerializer,
    DestinationListSerializer,
    PlaceDetailSerializer,
    PlaceListSerializer,
    PlaceWriteSerializer,
)


def _published_only(request):
    """Admin hammasini ko'radi, qolganlar faqat e'lon qilinganlarni."""
    return not (request.user and request.user.is_staff)


class DestinationViewSet(viewsets.ModelViewSet):
    """Shaharlar / hududlar. O'qish — hammaga, yozish — admin."""

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    search_fields = ["name", "region", "short_description"]
    ordering_fields = ["name", "sort_order"]
    filterset_fields = ["is_featured", "region"]

    def get_queryset(self):
        qs = Destination.objects.annotate(
            places_count=Count("places", filter=Q(places__is_published=True))
        ).order_by("sort_order", "name")
        if _published_only(self.request):
            qs = qs.filter(is_published=True)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return DestinationListSerializer
        return DestinationDetailSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    """Diqqatga sazovor joylar. Filtr: ?destination=samarqand&category=museum&is_free=true"""

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    filterset_class = PlaceFilter
    search_fields = ["name", "short_description", "description", "destination__name"]
    ordering_fields = ["name", "entry_fee_uzs", "visit_duration_minutes", "created_at"]

    def get_queryset(self):
        qs = Place.objects.select_related("destination")
        if self.action == "retrieve":
            qs = qs.prefetch_related("images")
        if _published_only(self.request):
            qs = qs.filter(is_published=True, destination__is_published=True)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return PlaceListSerializer
        if self.action == "retrieve":
            return PlaceDetailSerializer
        return PlaceWriteSerializer
