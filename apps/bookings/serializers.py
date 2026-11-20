from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.agencies.serializers import AgencyShortSerializer
from apps.tours.pricing import installment
from apps.tours.serializers import InstallmentSerializer

from .models import Booking, Traveler


class TravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traveler
        fields = ["full_name", "phone", "birth_date"]


class BookingTourSerializer(serializers.Serializer):
    slug = serializers.CharField()
    title = serializers.CharField()
    duration_days = serializers.IntegerField()
    meeting_point = serializers.CharField()


class BookingCreateSerializer(serializers.Serializer):
    departure = serializers.IntegerField(help_text="Jo'nash sanasi ID (tur sahifasidagi `departures[].id`)")
    seats = serializers.IntegerField(min_value=1, max_value=50)
    contact_name = serializers.CharField(max_length=200)
    contact_phone = serializers.CharField(max_length=30)
    contact_email = serializers.EmailField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    travelers = TravelerSerializer(many=True, required=False, default=list)


class BookingSerializer(serializers.ModelSerializer):
    tour = BookingTourSerializer(read_only=True)
    agency = AgencyShortSerializer(read_only=True)
    departure_date = serializers.DateField(source="departure.date", read_only=True)
    travelers = TravelerSerializer(many=True, read_only=True)
    installment = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "code",
            "status",
            "tour",
            "agency",
            "departure",
            "departure_date",
            "departure_at",
            "seats",
            "unit_price_uzs",
            "total_uzs",
            "installment",
            "cancellation_policy",
            "contact_name",
            "contact_phone",
            "contact_email",
            "note",
            "travelers",
            "expires_at",
            "confirmed_at",
            "cancelled_at",
            "cancelled_by",
            "cancel_reason",
            "refund_uzs",
            "created_at",
        ]
        read_only_fields = fields

    @extend_schema_field(InstallmentSerializer)
    def get_installment(self, booking):
        return installment(booking.total_uzs)


class CabinetBookingSerializer(BookingSerializer):
    """Agentlik ko'radigan bron: + moliyaviy taqsimot va turist emaili."""

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + [
            "user_email",
            "commission_percent",
            "commission_uzs",
            "agency_amount_uzs",
        ]
        read_only_fields = fields


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class CancelPreviewSerializer(serializers.Serializer):
    can_cancel = serializers.BooleanField()
    refund_uzs = serializers.IntegerField()
    cancellation_policy = serializers.CharField()
    policy_text = serializers.CharField()
