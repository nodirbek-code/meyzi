from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.phones import VerifiedPhoneMixin
from apps.accounts.serializers import phone_token_field
from apps.catalog.models import Destination
from apps.catalog.serializers import DestinationShortSerializer
from apps.core.files import document_rule

from .models import (
    GuideBooking,
    GuideMeetingPoint,
    GuideProfile,
    GuideReview,
    GuideUnavailableDate,
    Specialization,
    SpokenLanguage,
)


class _ChoiceList(serializers.ListField):
    def __init__(self, choices, **kwargs):
        super().__init__(child=serializers.ChoiceField(choices=choices), **kwargs)

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        return list(dict.fromkeys(values))  # takrorlarsiz, tartib saqlanadi


class GuideCardSerializer(serializers.ModelSerializer):
    destinations = DestinationShortSerializer(many=True, read_only=True)

    class Meta:
        model = GuideProfile
        fields = [
            "id",
            "slug",
            "display_name",
            "photo",
            "languages",
            "specializations",
            "destinations",
            "experience_years",
            "is_certified",
            "price_half_day_uzs",
            "price_full_day_uzs",
            "price_per_day_uzs",
            "rating",
            "reviews_count",
        ]


class MeetingPointSerializer(serializers.ModelSerializer):
    destination = serializers.SlugRelatedField(slug_field="slug", queryset=Destination.objects.all())

    class Meta:
        model = GuideMeetingPoint
        fields = ["id", "destination", "name", "address", "latitude", "longitude", "is_active"]

    def validate_destination(self, value):
        guide = self.context["request"].guide
        if not guide.destinations.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Bu shahar profilingizdagi shaharlar ro'yxatida yo'q.")
        return value

    def validate(self, attrs):
        guide = self.context["request"].guide
        destination = attrs.get("destination", getattr(self.instance, "destination", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        dup = GuideMeetingPoint.objects.filter(guide=guide, destination=destination, name=name)
        if self.instance:
            dup = dup.exclude(pk=self.instance.pk)
        if dup.exists():
            raise serializers.ValidationError({"name": "Bu shaharda shu nomli uchrashuv joyi bor."})
        return attrs


class PublicMeetingPointSerializer(serializers.ModelSerializer):
    destination = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = GuideMeetingPoint
        fields = ["id", "destination", "name", "address", "latitude", "longitude"]
        read_only_fields = fields


class GuideDetailSerializer(GuideCardSerializer):
    meeting_points = serializers.SerializerMethodField()

    class Meta(GuideCardSerializer.Meta):
        fields = GuideCardSerializer.Meta.fields + [
            "bio",
            "group_surcharge_percent",
            "max_group_size",
            "meeting_points",
        ]

    @extend_schema_field(PublicMeetingPointSerializer(many=True))
    def get_meeting_points(self, guide):
        points = [p for p in guide.meeting_points.all() if p.is_active]
        return PublicMeetingPointSerializer(points, many=True).data


class MyGuideProfileSerializer(VerifiedPhoneMixin, serializers.ModelSerializer):
    """Gid o'z profilini yaratadi/tahrirlaydi. Holat, komissiya, sertifikat tasdig'i — faqat admin.

    Sertifikat fayli yopiq saqlanadi va hech kimga qaytarilmaydi (faqat `has_certificate_file`).
    """

    certificate_file = serializers.FileField(write_only=True, required=False, validators=[document_rule])
    has_certificate_file = serializers.SerializerMethodField()
    phone_token = phone_token_field()

    languages = _ChoiceList(SpokenLanguage.choices, min_length=1)
    specializations = _ChoiceList(Specialization.choices, required=False)
    destinations = serializers.SlugRelatedField(
        slug_field="slug", many=True, queryset=Destination.objects.filter(is_published=True)
    )

    class Meta:
        model = GuideProfile
        fields = [
            "id",
            "slug",
            "display_name",
            "photo",
            "bio",
            "phone",
            "phone_token",
            "languages",
            "specializations",
            "destinations",
            "experience_years",
            "certificate_number",
            "certificate_file",
            "has_certificate_file",
            "is_certified",
            "price_half_day_uzs",
            "price_full_day_uzs",
            "price_per_day_uzs",
            "group_surcharge_percent",
            "max_group_size",
            "status",
            "moderation_note",
            "commission_percent",
            "rating",
            "reviews_count",
            "warnings_count",
            "no_show_count",
        ]
        read_only_fields = [
            "slug",
            "is_certified",
            "status",
            "moderation_note",
            "commission_percent",
            "rating",
            "reviews_count",
            "warnings_count",
            "no_show_count",
        ]

    def get_has_certificate_file(self, profile) -> bool:
        return bool(profile.certificate_file)

    def validate_destinations(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta shahar tanlang.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)  # telefon — akkauntdagi (bot orqali tasdiqlangan) raqam
        if self.instance is None:  # ariza: o'z rasmi va sertifikat majburiy
            missing = {}
            if not attrs.get("photo"):
                missing["photo"] = "O'zingizning rasmingizni yuklang (jpg, png yoki webp, 6 MB gacha)."
            if not attrs.get("certificate_file"):
                missing["certificate_file"] = "Gid sertifikatini yuklang (pdf, jpg yoki png, 6 MB gacha)."
            if missing:
                raise serializers.ValidationError(missing)
        for field in ("price_half_day_uzs", "price_full_day_uzs", "price_per_day_uzs"):
            if field in attrs and attrs[field] <= 0:
                raise serializers.ValidationError({field: "Narx 0 dan katta bo'lishi kerak."})
        return attrs


class QuoteQuerySerializer(serializers.Serializer):
    duration = serializers.ChoiceField(choices=GuideBooking.Duration.choices)
    days = serializers.IntegerField(min_value=1, max_value=14, default=1)
    group_size = serializers.IntegerField(min_value=1, max_value=50, default=1)


class QuoteSerializer(serializers.Serializer):
    duration = serializers.CharField()
    days = serializers.IntegerField()
    group_size = serializers.IntegerField()
    unit_price_uzs = serializers.IntegerField()
    base_uzs = serializers.IntegerField()
    surcharge_uzs = serializers.IntegerField()
    total_uzs = serializers.IntegerField()


class UnavailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuideUnavailableDate
        fields = ["id", "date", "note"]

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("O'tgan sana.")
        return value


class GuideBookingCreateSerializer(VerifiedPhoneMixin, serializers.Serializer):
    verified_phone_field = "contact_phone"

    guide = serializers.SlugRelatedField(slug_field="slug", queryset=GuideProfile.objects.all())
    destination = serializers.SlugRelatedField(slug_field="slug", queryset=Destination.objects.all())
    duration = serializers.ChoiceField(choices=GuideBooking.Duration.choices)
    start_date = serializers.DateField()
    start_time = serializers.TimeField()
    days = serializers.IntegerField(min_value=1, max_value=14, default=1)
    group_size = serializers.IntegerField(min_value=1, max_value=50)
    language = serializers.ChoiceField(choices=SpokenLanguage.choices)
    meeting_point = serializers.PrimaryKeyRelatedField(
        queryset=GuideMeetingPoint.objects.filter(is_active=True),
        help_text="Gid sahifasidagi `meeting_points[].id` — erkin matn qabul qilinmaydi",
        error_messages={
            "does_not_exist": "Gid belgilagan uchrashuv joylaridan birini tanlang.",
            "incorrect_type": "Gid belgilagan uchrashuv joylaridan birini tanlang.",
            "required": "Uchrashuv joyini tanlang.",
        },
    )
    contact_name = serializers.CharField(max_length=200)
    contact_phone = serializers.CharField(max_length=30)
    phone_token = phone_token_field()
    note = serializers.CharField(required=False, allow_blank=True, default="")


class GuideShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuideProfile
        fields = ["slug", "display_name", "photo", "phone", "rating"]


class GuideBookingSerializer(serializers.ModelSerializer):
    guide = GuideShortSerializer(read_only=True)
    destination = DestinationShortSerializer(read_only=True)
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = GuideBooking
        fields = [
            "code",
            "status",
            "guide",
            "destination",
            "duration",
            "start_date",
            "days",
            "start_time",
            "starts_at",
            "group_size",
            "language",
            "unit_price_uzs",
            "base_uzs",
            "surcharge_uzs",
            "total_uzs",
            "meeting_point",
            "meeting_latitude",
            "meeting_longitude",
            "note",
            "contact_name",
            "contact_phone",
            "respond_by",
            "accepted_at",
            "confirmed_at",
            "decline_reason",
            "cancelled_at",
            "cancelled_by",
            "cancel_reason",
            "refund_uzs",
            "no_show",
            "has_review",
            "created_at",
        ]
        read_only_fields = fields

    def get_has_review(self, booking) -> bool:
        return hasattr(booking, "review")

    def to_representation(self, booking):
        data = super().to_representation(booking)
        # Gid telefoni faqat to'lovdan keyin (taqdimot: kontakt to'g'ridan berilmaydi, platforma orqali)
        if booking.status not in (GuideBooking.Status.CONFIRMED, GuideBooking.Status.COMPLETED):
            data["guide"]["phone"] = None
        return data


class CabinetGuideBookingSerializer(GuideBookingSerializer):
    class Meta(GuideBookingSerializer.Meta):
        fields = GuideBookingSerializer.Meta.fields + [
            "commission_percent",
            "commission_uzs",
            "guide_amount_uzs",
            "guide_penalty_usd",
            "guide_warnings",
        ]
        read_only_fields = fields

    def to_representation(self, booking):
        data = serializers.ModelSerializer.to_representation(self, booking)
        if booking.status not in (GuideBooking.Status.CONFIRMED, GuideBooking.Status.COMPLETED):
            data["contact_phone"] = None  # turist telefoni ham to'lovdan keyin
        return data


class GuideReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class GuideReviewSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = GuideReview
        fields = ["id", "author", "rating", "text", "guide_reply", "created_at"]
        read_only_fields = fields

    def get_author(self, review) -> str:
        u = review.user
        name = (u.first_name or "").strip() or "Sayohatchi"
        return f"{name} {u.last_name[:1]}." if u.last_name else name


class GuideReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(required=False, allow_blank=True, default="", max_length=3000)
