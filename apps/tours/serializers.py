from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.agencies.serializers import AgencyShortSerializer
from apps.agencies.services import unique_slug
from apps.catalog.models import Destination, Place
from apps.catalog.serializers import DestinationShortSerializer

from .models import Departure, ItineraryDay, ItineraryItem, Tour, TourCategory, TourMedia
from .policies import POLICY_TEXT
from .pricing import installment


class InstallmentSerializer(serializers.Serializer):
    months = serializers.IntegerField()
    monthly_uzs = serializers.IntegerField()
    total_uzs = serializers.IntegerField()


class TourCategorySerializer(serializers.ModelSerializer):
    tours_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TourCategory
        fields = ["id", "name", "slug", "icon", "tours_count"]


class CategoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourCategory
        fields = ["name", "slug"]


class TourMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourMedia
        fields = ["id", "kind", "file", "caption", "is_cover", "sort_order"]


class ItineraryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryItem
        fields = ["start_time", "end_time", "title", "description", "is_extra_cost"]


class ItineraryDaySerializer(serializers.ModelSerializer):
    items = ItineraryItemSerializer(many=True, required=False)

    class Meta:
        model = ItineraryDay
        fields = ["day_number", "title", "description", "items"]


class DepartureSerializer(serializers.ModelSerializer):
    seats_left = serializers.IntegerField(read_only=True)
    price_uzs = serializers.IntegerField(source="effective_price", read_only=True)
    is_bookable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Departure
        fields = ["id", "date", "seats_left", "price_uzs", "is_bookable"]


def _upcoming(tour):
    """Prefetch qilingan (`upcoming_departures`) yoki bazadan — kelgusi ochiq sanalar."""
    if hasattr(tour, "upcoming_departures"):
        return tour.upcoming_departures
    return list(
        tour.departures.filter(status=Departure.Status.OPEN, date__gte=timezone.localdate()).order_by("date")
    )


class TourCardSerializer(serializers.ModelSerializer):
    """Turlar ro'yxatidagi kartochka."""

    destination = DestinationShortSerializer(read_only=True)
    agency = AgencyShortSerializer(read_only=True)
    categories = CategoryShortSerializer(many=True, read_only=True)
    cover = serializers.SerializerMethodField()
    installment = serializers.SerializerMethodField()
    next_departure = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = [
            "id",
            "slug",
            "title",
            "short_description",
            "cover",
            "categories",
            "destination",
            "agency",
            "duration_days",
            "duration_nights",
            "price_uzs",
            "installment",
            "next_departure",
            "cancellation_policy",
            "rating",
            "reviews_count",
            "is_featured",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_cover(self, tour):
        media = list(tour.media.all())
        image = next((m for m in media if m.kind == TourMedia.Kind.IMAGE), None)
        if not image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.file.url) if request else image.file.url

    @extend_schema_field(InstallmentSerializer)
    def get_installment(self, tour):
        return installment(tour.price_uzs)

    @extend_schema_field(DepartureSerializer(allow_null=True))
    def get_next_departure(self, tour):
        nxt = next((d for d in _upcoming(tour) if d.seats_left > 0), None)
        return DepartureSerializer(nxt).data if nxt else None


class TourDetailSerializer(TourCardSerializer):
    media = TourMediaSerializer(many=True, read_only=True)
    itinerary = ItineraryDaySerializer(many=True, read_only=True)
    departures = serializers.SerializerMethodField()
    cancellation_policy_text = serializers.SerializerMethodField()
    places = serializers.SlugRelatedField(many=True, read_only=True, slug_field="slug")

    class Meta(TourCardSerializer.Meta):
        fields = TourCardSerializer.Meta.fields + [
            "description",
            "max_group_size",
            "departure_time",
            "return_time",
            "meeting_point",
            "meeting_latitude",
            "meeting_longitude",
            "meeting_map_url",
            "price_note",
            "cancellation_policy_text",
            "included",
            "not_included",
            "what_to_bring",
            "media",
            "itinerary",
            "departures",
            "places",
        ]

    @extend_schema_field(DepartureSerializer(many=True))
    def get_departures(self, tour):
        return DepartureSerializer(_upcoming(tour), many=True).data

    def get_cancellation_policy_text(self, tour) -> str:
        return POLICY_TEXT[tour.cancellation_policy]


# ---------- Agentlik kabineti ----------


class StringListField(serializers.ListField):
    child = serializers.CharField(max_length=300)


class CabinetTourSerializer(serializers.ModelSerializer):
    """Agentlik turini yaratish/tahrirlash. `itinerary` yuborilsa — butunlay almashtiriladi."""

    destination = serializers.SlugRelatedField(slug_field="slug", queryset=Destination.objects.all())
    categories = serializers.SlugRelatedField(
        slug_field="slug", many=True, queryset=TourCategory.objects.filter(is_active=True)
    )
    places = serializers.SlugRelatedField(
        slug_field="slug", many=True, queryset=Place.objects.all(), required=False
    )
    itinerary = ItineraryDaySerializer(many=True, required=False)
    included = StringListField(required=False)
    not_included = StringListField(required=False)
    what_to_bring = StringListField(required=False)
    media = TourMediaSerializer(many=True, read_only=True)
    installment = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = [
            "id",
            "slug",
            "title",
            "short_description",
            "description",
            "destination",
            "categories",
            "places",
            "duration_days",
            "duration_nights",
            "max_group_size",
            "departure_time",
            "return_time",
            "meeting_point",
            "meeting_latitude",
            "meeting_longitude",
            "meeting_map_url",
            "price_uzs",
            "price_note",
            "installment",
            "cancellation_policy",
            "included",
            "not_included",
            "what_to_bring",
            "itinerary",
            "media",
            "status",
            "moderation_note",
            "published_at",
            "rating",
            "reviews_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "slug",
            "status",
            "moderation_note",
            "published_at",
            "rating",
            "reviews_count",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(InstallmentSerializer)
    def get_installment(self, tour):
        return installment(tour.price_uzs)

    def validate_categories(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta toifa tanlang.")
        return value

    def validate_price_uzs(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return value

    def validate_meeting_point(self, value):
        if not value.strip():
            raise serializers.ValidationError("Uchrashuv joyini kiriting.")
        return value.strip()

    def validate(self, attrs):
        lat = attrs.get("meeting_latitude", getattr(self.instance, "meeting_latitude", None))
        lng = attrs.get("meeting_longitude", getattr(self.instance, "meeting_longitude", None))
        if (lat is None) != (lng is None):
            raise serializers.ValidationError(
                {"meeting_latitude": "Kenglik va uzunlik ikkalasi birga kiritiladi."}
            )
        days = attrs.get("duration_days", getattr(self.instance, "duration_days", 1))
        itinerary = attrs.get("itinerary")
        if itinerary is not None:
            numbers = [d["day_number"] for d in itinerary]
            if len(numbers) != len(set(numbers)):
                raise serializers.ValidationError({"itinerary": "Kun raqamlari takrorlanmasligi kerak."})
            if any(n < 1 or n > days for n in numbers):
                raise serializers.ValidationError(
                    {"itinerary": f"Kun raqami 1 dan {days} gacha bo'lishi kerak."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        itinerary = validated_data.pop("itinerary", None)
        categories = validated_data.pop("categories")
        places = validated_data.pop("places", [])
        validated_data["slug"] = unique_slug(Tour, validated_data["title"])
        tour = Tour.objects.create(**validated_data)
        tour.categories.set(categories)
        tour.places.set(places)
        if itinerary is not None:
            self._save_itinerary(tour, itinerary)
        return tour

    @transaction.atomic
    def update(self, tour, validated_data):
        itinerary = validated_data.pop("itinerary", None)
        categories = validated_data.pop("categories", None)
        places = validated_data.pop("places", None)
        for key, value in validated_data.items():
            setattr(tour, key, value)
        tour.save()
        if categories is not None:
            tour.categories.set(categories)
        if places is not None:
            tour.places.set(places)
        if itinerary is not None:
            self._save_itinerary(tour, itinerary)
        return tour

    @staticmethod
    def _save_itinerary(tour, itinerary):
        tour.itinerary.all().delete()
        for day_data in itinerary:
            items = day_data.pop("items", [])
            day = ItineraryDay.objects.create(tour=tour, **day_data)
            ItineraryItem.objects.bulk_create(
                [ItineraryItem(day=day, sort_order=i, **item) for i, item in enumerate(items)]
            )


class CabinetDepartureSerializer(serializers.ModelSerializer):
    seats_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Departure
        fields = ["id", "date", "seats_total", "seats_booked", "seats_left", "price_uzs", "status"]
        read_only_fields = ["seats_booked"]

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("O'tib ketgan sana qo'shib bo'lmaydi.")
        tour = self.context["tour"]
        clash = Departure.objects.filter(tour=tour, date=value)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError("Bu sana allaqachon qo'shilgan.")
        return value

    def validate_seats_total(self, value):
        if value < 1:
            raise serializers.ValidationError("Kamida 1 ta joy bo'lishi kerak.")
        if self.instance and value < self.instance.seats_booked:
            raise serializers.ValidationError(
                f"Allaqachon {self.instance.seats_booked} ta joy band — undan kam qilib bo'lmaydi."
            )
        return value


class CabinetMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourMedia
        fields = ["id", "kind", "file", "caption", "is_cover", "sort_order"]

    def validate(self, attrs):
        from apps.core.files import image_rule, video_rule

        kind = attrs.get("kind", getattr(self.instance, "kind", TourMedia.Kind.IMAGE))
        f = attrs.get("file")
        if f is not None:
            rule = video_rule if kind == TourMedia.Kind.VIDEO else image_rule
            try:
                rule(f)
            except Exception as exc:  # django ValidationError → DRF
                raise serializers.ValidationError(
                    {"file": list(getattr(exc, "messages", [str(exc)]))}
                ) from None
        if kind == TourMedia.Kind.VIDEO and attrs.get("is_cover"):
            raise serializers.ValidationError({"is_cover": "Muqova faqat rasm bo'lishi mumkin."})
        return attrs
