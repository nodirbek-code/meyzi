from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Ommaviy sharh."""

    author = serializers.SerializerMethodField()
    tour = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    tour_title = serializers.CharField(source="tour.title", read_only=True)
    agency = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "author",
            "tour",
            "tour_title",
            "agency",
            "rating",
            "text",
            "agency_reply",
            "agency_replied_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_author(self, review) -> str:
        """Maxfiylik: ism + familiyaning bosh harfi."""
        u = review.user
        name = (u.first_name or "").strip() or "Sayohatchi"
        return f"{name} {u.last_name[:1]}.".strip() if u.last_name else name


class MyReviewSerializer(ReviewSerializer):
    booking = serializers.CharField(source="booking.code", read_only=True)

    class Meta(ReviewSerializer.Meta):
        fields = ReviewSerializer.Meta.fields + ["booking", "status", "moderation_note"]
        read_only_fields = fields


class ReviewCreateSerializer(serializers.Serializer):
    booking = serializers.CharField(help_text="Bron raqami (LZ...)")
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(required=False, allow_blank=True, default="", max_length=3000)


class ReviewUpdateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    text = serializers.CharField(required=False, allow_blank=True, max_length=3000)


class AgencyReplySerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=True, max_length=2000)
