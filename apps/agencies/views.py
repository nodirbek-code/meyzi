from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.notifications import services as notify

from . import services
from .models import Agency, AgencyApplication
from .permissions import IsAgencyMember
from .serializers import (
    AgencyApplicationAdminSerializer,
    AgencyApplicationSerializer,
    AgencySerializer,
    CabinetAgencySerializer,
    RejectSerializer,
)


class AgencyViewSet(viewsets.ReadOnlyModelViewSet):
    """Faol agentliklar (ommaviy)."""

    serializer_class = AgencySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    search_fields = ["name"]
    filterset_fields = ["is_verified", "is_platform"]
    ordering_fields = ["name", "rating"]

    def get_queryset(self):
        from apps.tours.models import Tour

        return (
            Agency.objects.filter(status=Agency.Status.ACTIVE, moderation_status=Agency.Moderation.APPROVED)
            .annotate(tours_count=Count("tours", filter=Q(tours__status=Tour.Status.PUBLISHED)))
            .order_by("-is_platform", "name")
        )


class AgencyApplicationViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    POST — ariza yuborish (hamma, login shart emas).
    GET — admin: barcha arizalar; foydalanuvchi: o'z arizalari.
    approve / reject — faqat admin.
    """

    filterset_fields = ["status"]
    search_fields = ["agency_name", "contact_person", "phone"]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        if self.action in ("approve", "reject"):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "auth"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AgencyApplication.objects.none()
        qs = AgencyApplication.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    def get_serializer_class(self):
        if getattr(self, "swagger_fake_view", False):
            return AgencyApplicationSerializer
        if self.request.user.is_staff and self.action != "create":
            return AgencyApplicationAdminSerializer
        return AgencyApplicationSerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        application = serializer.save(user=user)
        notify.agency_application_created(application)

    @extend_schema(request=None, responses=AgencySerializer)
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        agency = services.approve_application(self.get_object(), reviewer=request.user)
        return Response(AgencySerializer(agency, context={"request": request}).data, status=201)

    @extend_schema(request=RejectSerializer, responses=AgencyApplicationAdminSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        ser = RejectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        application = services.reject_application(
            self.get_object(), reviewer=request.user, note=ser.validated_data["note"]
        )
        return Response(AgencyApplicationAdminSerializer(application).data)


class CabinetAgencyView(generics.RetrieveUpdateAPIView):
    """Agentlik kabineti: o'z profili."""

    serializer_class = CabinetAgencySerializer
    permission_classes = [IsAgencyMember]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.agency

    def perform_update(self, serializer):
        agency = serializer.save()
        services.submit_agency_changes(agency)  # admin tasdiqlaguncha sahifa va turlar yashirin
