from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.phones import VerifiedPhoneMixin, normalize_phone
from apps.accounts.serializers import phone_token_field
from apps.agencies.serializers import AgencyShortSerializer
from apps.tours.pricing import installment
from apps.tours.serializers import InstallmentSerializer

from .models import Booking, Traveler


class TravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traveler
        fields = ["full_name", "phone", "birth_date"]

    def validate_phone(self, value):
        # sayohatchining telefoni ixtiyoriy, lekin yozilsa — to'g'ri format (+998 XX XXX XX XX)
        if not (value or "").strip():
            return ""
        return _phone_or_error(value)


class BookingTourSerializer(serializers.Serializer):
    slug = serializers.CharField()
    title = serializers.CharField()
    duration_days = serializers.IntegerField()
    meeting_point = serializers.CharField()
    meeting_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    meeting_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    meeting_map_url = serializers.CharField()
    cover = serializers.SerializerMethodField()

    def get_cover(self, tour) -> str | None:
        from apps.tours.models import TourMedia

        image = next((m for m in tour.media.all() if m.kind == TourMedia.Kind.IMAGE), None)
        if not image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.file.url) if request else image.file.url


def _phone_or_error(value):
    from rest_framework.exceptions import ValidationError

    from apps.accounts.phones import INVALID_TEXT

    try:
        return normalize_phone(value)
    except ValidationError:
        raise serializers.ValidationError(INVALID_TEXT) from None


class BookingCreateSerializer(VerifiedPhoneMixin, serializers.Serializer):
    """Aloqa telefoni Telegram kodi bilan tasdiqlanadi (yoki akkauntdagi tasdiqlangan raqam)."""

    verified_phone_field = "contact_phone"

    departure = serializers.IntegerField(help_text="Jo'nash sanasi ID (tur sahifasidagi `departures[].id`)")
    seats = serializers.IntegerField(min_value=1, max_value=50)
    contact_name = serializers.CharField(max_length=200)
    contact_phone = serializers.CharField(max_length=30)
    phone_token = phone_token_field()
    contact_email = serializers.EmailField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    travelers = TravelerSerializer(many=True, required=False, default=list)


class BookingSerializer(serializers.ModelSerializer):
    tour = BookingTourSerializer(read_only=True)
    agency = AgencyShortSerializer(read_only=True)
    departure_date = serializers.DateField(source="departure.date", read_only=True)
    travelers = TravelerSerializer(many=True, read_only=True)
    installment = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()

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
            "has_review",
            "created_at",
        ]
        read_only_fields = fields

    def get_has_review(self, booking) -> bool:
        return hasattr(booking, "review")

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
