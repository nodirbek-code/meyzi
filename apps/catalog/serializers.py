from rest_framework import serializers

from .models import Destination, Place, PlaceImage


class DestinationListSerializer(serializers.ModelSerializer):
    places_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Destination
        fields = [
            "id",
            "name",
            "slug",
            "region",
            "short_description",
            "cover_image",
            "latitude",
            "longitude",
            "is_featured",
            "places_count",
        ]


class DestinationDetailSerializer(DestinationListSerializer):
    class Meta(DestinationListSerializer.Meta):
        fields = DestinationListSerializer.Meta.fields + ["description"]


class PlaceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceImage
        fields = ["id", "image", "caption"]


class DestinationShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "name", "slug"]


class PlaceListSerializer(serializers.ModelSerializer):
    destination = DestinationShortSerializer(read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Place
        fields = [
            "id",
            "name",
            "slug",
            "destination",
            "category",
            "category_display",
            "short_description",
            "cover_image",
            "latitude",
            "longitude",
            "entry_fee_uzs",
            "is_free",
            "visit_duration_minutes",
            "is_featured",
        ]


class PlaceDetailSerializer(PlaceListSerializer):
    images = PlaceImageSerializer(many=True, read_only=True)

    class Meta(PlaceListSerializer.Meta):
        fields = PlaceListSerializer.Meta.fields + [
            "description",
            "history",
            "address",
            "opening_hours",
            "audio_guide",
            "images",
        ]


class PlaceWriteSerializer(serializers.ModelSerializer):
    """Admin uchun yaratish/tahrirlash."""

    class Meta:
        model = Place
        exclude = ["created_at", "updated_at"]
