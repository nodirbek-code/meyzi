from rest_framework import serializers

from apps.catalog.models import Destination
from apps.catalog.serializers import DestinationShortSerializer

from .models import Amenity, Hotel, HotelBooking, HotelImage, HotelReview, RoomType


class _AmenityList(serializers.ListField):
    child = serializers.ChoiceField(choices=Amenity.choices)

    def to_internal_value(self, data):
        return list(dict.fromkeys(super().to_internal_value(data)))


class HotelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelImage
        fields = ["id", "image", "caption", "is_cover", "sort_order"]


class RoomTypeSerializer(serializers.ModelSerializer):
    amenities = _AmenityList(required=False)

    class Meta:
        model = RoomType
        fields = [
            "id",
            "name",
            "description",
            "capacity",
            "beds",
            "size_m2",
            "price_per_night_uzs",
            "total_rooms",
            "amenities",
            "image",
            "is_active",
        ]

    def validate_price_per_night_uzs(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return value


class RoomOfferSerializer(serializers.Serializer):
    """Sanalar berilganda xona turi: bo'sh xonalar va butun muddat narxi."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    capacity = serializers.IntegerField()
    beds = serializers.CharField()
    size_m2 = serializers.IntegerField(allow_null=True)
    price_per_night_uzs = serializers.IntegerField()
    amenities = serializers.ListField(child=serializers.CharField())
    image = serializers.CharField(allow_null=True)
    available_rooms = serializers.IntegerField(allow_null=True)
    nights = serializers.IntegerField(allow_null=True)
    stay_total_uzs = serializers.IntegerField(allow_null=True, help_text="1 xona, butun muddat")


class HotelCardSerializer(serializers.ModelSerializer):
    destination = DestinationShortSerializer(read_only=True)
    cover = serializers.SerializerMethodField()
    min_price_uzs = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Hotel
        fields = [
            "id",
            "slug",
            "name",
            "kind",
            "stars",
            "destination",
            "address",
            "cover",
            "amenities",
            "min_price_uzs",
            "cancellation_policy",
            "rating",
            "reviews_count",
            "is_featured",
        ]

    def get_cover(self, hotel) -> str | None:
        images = list(hotel.images.all())
        if not images:
            return None
        request = self.context.get("request")
        url = images[0].image.url
        return request.build_absolute_uri(url) if request else url


class HotelDetailSerializer(HotelCardSerializer):
    images = HotelImageSerializer(many=True, read_only=True)
    cancellation_policy_text = serializers.SerializerMethodField()

    class Meta(HotelCardSerializer.Meta):
        fields = HotelCardSerializer.Meta.fields + [
            "description",
            "latitude",
            "longitude",
            "check_in_time",
            "check_out_time",
            "cancellation_policy_text",
            "images",
        ]

    def get_cancellation_policy_text(self, hotel) -> str:
        from apps.tours.policies import POLICY_TEXT

        return (
            POLICY_TEXT[hotel.cancellation_policy].replace("Jo'nash", "Kirish").replace("jo'nash", "kirish")
        )


class MyHotelSerializer(serializers.ModelSerializer):
    """Mehmonxona egasi: ariza va profil. Holat, komissiya, reyting — faqat admin."""

    destination = serializers.SlugRelatedField(slug_field="slug", queryset=Destination.objects.all())
    amenities = _AmenityList(required=False)

    class Meta:
        model = Hotel
        fields = [
            "id",
            "slug",
            "name",
            "kind",
            "destination",
            "stars",
            "description",
            "address",
            "latitude",
            "longitude",
            "phone",
            "email",
            "amenities",
            "check_in_time",
            "check_out_time",
            "cancellation_policy",
            "status",
            "moderation_note",
            "commission_percent",
            "rating",
            "reviews_count",
        ]
        read_only_fields = [
            "slug",
            "status",
            "moderation_note",
            "commission_percent",
            "rating",
            "reviews_count",
        ]


class AvailabilityQuerySerializer(serializers.Serializer):
    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)
    guests = serializers.IntegerField(min_value=1, max_value=60, required=False, default=1)
    rooms = serializers.IntegerField(min_value=1, max_value=20, required=False, default=1)

    def validate(self, attrs):
        if bool(attrs.get("check_in")) != bool(attrs.get("check_out")):
            raise serializers.ValidationError("check_in va check_out ikkalasi birga beriladi.")
        if attrs.get("check_in"):
            from .services import validate_stay

            attrs["nights"] = validate_stay(attrs["check_in"], attrs["check_out"])
        return attrs


class HotelBookingCreateSerializer(serializers.Serializer):
    room_type = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    rooms = serializers.IntegerField(min_value=1, max_value=20, default=1)
    guests = serializers.IntegerField(min_value=1, max_value=60)
    contact_name = serializers.CharField(max_length=200)
    contact_phone = serializers.CharField(max_length=30)
    contact_email = serializers.EmailField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")


class HotelShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ["slug", "name", "address", "phone", "check_in_time", "check_out_time"]


class HotelBookingSerializer(serializers.ModelSerializer):
    hotel = HotelShortSerializer(read_only=True)
    room_type = serializers.CharField(source="room_type.name", read_only=True)
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = HotelBooking
        fields = [
            "code",
            "status",
            "hotel",
            "room_type",
            "check_in",
            "check_out",
            "nights",
            "rooms",
            "guests",
            "price_per_night_uzs",
            "total_uzs",
            "cancellation_policy",
            "contact_name",
            "contact_phone",
            "contact_email",
            "note",
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


class CabinetHotelBookingSerializer(HotelBookingSerializer):
    class Meta(HotelBookingSerializer.Meta):
        fields = HotelBookingSerializer.Meta.fields + [
            "commission_percent",
            "commission_uzs",
            "hotel_amount_uzs",
        ]
        read_only_fields = fields


class HotelReviewSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = HotelReview
        fields = ["id", "author", "rating", "text", "hotel_reply", "created_at"]
        read_only_fields = fields

    def get_author(self, review) -> str:
        u = review.user
        name = (u.first_name or "").strip() or "Mehmon"
        return f"{name} {u.last_name[:1]}." if u.last_name else name


class HotelReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(required=False, allow_blank=True, default="", max_length=3000)


class ReplySerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=True, max_length=2000)


class HotelReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
