from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

# Ro'yxatdan o'tishda tanlash mumkin bo'lgan rollar (admin — faqat ichkaridan)
PUBLIC_ROLES = [User.Role.TOURIST, User.Role.GUIDE, User.Role.BUSINESS]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "language",
            "country",
            "avatar",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "date_joined", "full_name"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    role = serializers.ChoiceField(
        choices=[(r.value, r.label) for r in PUBLIC_ROLES], default=User.Role.TOURIST
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone", "role", "language", "country"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu email bilan foydalanuvchi allaqachon mavjud.")
        return value

    def validate(self, attrs):
        user = User(**{k: v for k, v in attrs.items() if k != "password"})
        password_validation.validate_password(attrs["password"], user)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            "user": UserSerializer(instance, context=self.context).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class LoginSerializer(TokenObtainPairSerializer):
    """Email + parol -> access/refresh token va foydalanuvchi ma'lumoti."""

    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].lower()
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user, context=self.context).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
