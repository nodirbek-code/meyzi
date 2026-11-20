from rest_framework import serializers

from .models import Agency, AgencyApplication


class AgencyShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ["id", "name", "slug", "logo", "is_verified", "is_platform", "rating", "reviews_count"]


class AgencySerializer(serializers.ModelSerializer):
    tours_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Agency
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "description",
            "phone",
            "telegram",
            "website",
            "address",
            "is_verified",
            "is_platform",
            "rating",
            "reviews_count",
            "tours_count",
        ]


class CabinetAgencySerializer(serializers.ModelSerializer):
    """Agentlik o'z profilini tahrirlaydi. Holat, komissiya, tekshiruv — faqat admin."""

    class Meta:
        model = Agency
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "description",
            "phone",
            "email",
            "telegram",
            "website",
            "address",
            "inn",
            "license_number",
            "status",
            "is_verified",
            "is_platform",
            "auto_publish",
            "commission_percent",
            "rating",
            "reviews_count",
        ]
        read_only_fields = [
            "slug",
            "status",
            "is_verified",
            "is_platform",
            "auto_publish",
            "commission_percent",
            "rating",
            "reviews_count",
        ]


class AgencyApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyApplication
        fields = ["id", "agency_name", "contact_person", "phone", "email", "message", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]


class AgencyApplicationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyApplication
        fields = [
            "id",
            "agency_name",
            "contact_person",
            "phone",
            "email",
            "message",
            "user",
            "status",
            "admin_note",
            "reviewed_by",
            "reviewed_at",
            "agency",
            "created_at",
        ]
        read_only_fields = fields


class RejectSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="")
