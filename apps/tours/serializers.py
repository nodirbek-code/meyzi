from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.agencies.serializers import AgencyShortSerializer
from apps.agencies.services import unique_slug
from apps.catalog.models import Destination, Place
from apps.catalog.serializers import DestinationShortSerializer
from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel, HotelImage

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


class TourGuideSerializer(serializers.ModelSerializer):
    """Tur sahifasidagi gid kartasi — kontaktlarsiz (telefon faqat gid bronidan keyin ochiladi)."""

    class Meta:
        model = GuideProfile
        fields = ["slug", "display_name", "photo", "languages", "experience_years", "is_certified", "rating"]


class TourGuideOptionSerializer(serializers.Serializer):
    """Bron oynasi: shu sana uchun tanlash mumkin bo'lgan gid (kontaktlarsiz)."""

    slug = serializers.CharField(source="guide.slug")
    display_name = serializers.CharField(source="guide.display_name")
    photo = serializers.ImageField(source="guide.photo", allow_null=True)
    languages = serializers.ListField(source="guide.languages", child=serializers.CharField())
    experience_years = serializers.IntegerField(source="guide.experience_years")
    is_certified = serializers.BooleanField(source="guide.is_certified")
    rating = serializers.DecimalField(source="guide.rating", max_digits=3, decimal_places=2)
    available = serializers.BooleanField()


class TourHotelSerializer(serializers.ModelSerializer):
    destination = serializers.CharField(source="destination.name", read_only=True)
    cover = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ["slug", "name", "kind", "stars", "destination", "cover", "rating"]

    def get_cover(self, hotel) -> str | None:
        image = next((i for i in hotel.images.all() if i.kind == HotelImage.Kind.IMAGE), None)
        if image is None:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.image.url) if request else image.image.url


class TourDetailSerializer(TourCardSerializer):
    media = TourMediaSerializer(many=True, read_only=True)
    itinerary = ItineraryDaySerializer(many=True, read_only=True)
    departures = serializers.SerializerMethodField()
    cancellation_policy_text = serializers.SerializerMethodField()
    places = serializers.SlugRelatedField(many=True, read_only=True, slug_field="slug")
    guides = TourGuideSerializer(many=True, read_only=True)  # view faqat tasdiqlanganlarini prefetch qiladi
    hotels = TourHotelSerializer(many=True, read_only=True)

    class Meta(TourCardSerializer.Meta):
        fields = TourCardSerializer.Meta.fields + [
            "description",
            "guide_price_uzs",
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
            "guides",
            "hotels",
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
    # Ixtiyoriy professional gidlar — faqat tasdiqlanganlar (slug'lar, /guides/ katalogidan)
    guides = serializers.SlugRelatedField(
        slug_field="slug",
        many=True,
        required=False,
        queryset=GuideProfile.objects.filter(status=GuideProfile.Status.APPROVED),
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
            "guides",
            "guide_price_uzs",
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
        guides = validated_data.pop("guides", [])
        validated_data["slug"] = unique_slug(Tour, validated_data["title"])
        tour = Tour.objects.create(**validated_data)
        tour.categories.set(categories)
        tour.places.set(places)
        tour.guides.set(guides)
        if itinerary is not None:
            self._save_itinerary(tour, itinerary)
        return tour

    @transaction.atomic
    def update(self, tour, validated_data):
        itinerary = validated_data.pop("itinerary", None)
        categories = validated_data.pop("categories", None)
        places = validated_data.pop("places", None)
        guides = validated_data.pop("guides", None)
        for key, value in validated_data.items():
            setattr(tour, key, value)
        tour.save()
        if categories is not None:
            tour.categories.set(categories)
        if places is not None:
            tour.places.set(places)
        if guides is not None:
            tour.guides.set(guides)
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
        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.core.files import check_gallery_limit, image_rule, media_kind, video_rule

        f = attrs.get("file")
        kind = attrs.get("kind", getattr(self.instance, "kind", TourMedia.Kind.IMAGE))
        if f is not None:
            # turi fayldan aniqlanadi (mijoz yuborgan qiymatga ishonilmaydi)
            kind = media_kind(f.name) or kind
            attrs["kind"] = kind
            rule = video_rule if kind == TourMedia.Kind.VIDEO else image_rule
            try:
                rule(f)
                check_gallery_limit(self._gallery(), kind, exclude_pk=getattr(self.instance, "pk", None))
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"file": list(exc.messages)}) from None
        if kind == TourMedia.Kind.VIDEO and attrs.get("is_cover"):
            raise serializers.ValidationError({"is_cover": "Muqova faqat rasm bo'lishi mumkin."})
        return attrs

    def _gallery(self):
        """Shu turning media'si: yangi faylda — view `context["tour"]` beradi, tahrirda — instance'dan."""
        tour = self.context.get("tour") or getattr(self.instance, "tour", None)
        return TourMedia.objects.filter(tour=tour) if tour is not None else TourMedia.objects.none()
