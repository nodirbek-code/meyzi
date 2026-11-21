from django.db import transaction
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from . import auth_services, google
from .serializers import (
    AuthResponseSerializer,
    ChangePasswordSerializer,
    CodeSerializer,
    EmailSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    PhoneChangeVerifySerializer,
    PhoneCheckResponseSerializer,
    PhoneSerializer,
    PhoneVerifySerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Ro'yxatdan o'tish. Javobda foydalanuvchi va JWT tokenlar; emailga tasdiqlash kodi yuboriladi."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def perform_create(self, serializer):
        user = serializer.save()
        auth_services.send_email_verification(user)


class LoginView(TokenObtainPairView):
    """Email + parol bilan kirish."""

    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class MeView(generics.RetrieveUpdateAPIView):
    """Joriy foydalanuvchi profili: ko'rish va tahrirlash."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={204: None})
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    """Refresh tokenni bekor qiladi (blacklist)."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Token yaroqsiz."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _tokens(user, request, **extra):
    refresh = RefreshToken.for_user(user)
    return {
        "user": UserSerializer(user, context={"request": request}).data,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        **extra,
    }


class _CodeView(APIView):
    """Kod yuborish/tekshirish view'lari: qat'iy throttling.

    `non_atomic_requests` — noto'g'ri kod urinishlari hisoblagichi so'rov xatosi bilan birga
    orqaga qaytmasligi uchun (aks holda 5 urinish cheklovi ishlamaydi).
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class PasswordForgotView(_CodeView):
    """Parolni tiklash kodi emailga yuboriladi. Javob doim bir xil (email bor-yo'qligi oshkor qilinmaydi)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=EmailSerializer, responses={200: dict})
    def post(self, request):
        ser = EmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        auth_services.request_password_reset(ser.validated_data["email"])
        return Response({"detail": "Agar bu email ro'yxatdan o'tgan bo'lsa, unga kod yuborildi."})


class PasswordResetView(_CodeView):
    """Kod + yangi parol. Muvaffaqiyatli bo'lsa — barcha qurilmalardan chiqariladi."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PasswordResetSerializer, responses={204: None})
    def post(self, request):
        ser = PasswordResetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        auth_services.reset_password(**ser.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailSendCodeView(_CodeView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        auth_services.send_email_verification(request.user)
        return Response({"detail": "Kod emailingizga yuborildi."})


class EmailVerifyView(_CodeView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=CodeSerializer, responses=UserSerializer)
    def post(self, request):
        ser = CodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = auth_services.verify_email(request.user, ser.validated_data["code"])
        return Response(UserSerializer(user, context={"request": request}).data)


TELEGRAM_SENT = "Tasdiqlash kodi Telegram'ga yuborildi."


class PhoneRequestCodeView(_CodeView):
    """Telefon orqali kirish/ro'yxatdan o'tish: kod shu raqamning Telegram akkauntiga yuboriladi."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PhoneSerializer, responses={200: dict})
    def post(self, request):
        ser = PhoneSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        auth_services.request_phone_login(ser.validated_data["phone"])
        return Response(
            {"detail": TELEGRAM_SENT, "phone": ser.validated_data["phone"], "channel": "telegram"}
        )


class PhoneVerifyView(_CodeView):
    """Kod to'g'ri bo'lsa — kirish (akkaunt bo'lmasa avtomatik yaratiladi, `is_new: true`)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PhoneVerifySerializer, responses=AuthResponseSerializer)
    def post(self, request):
        ser = PhoneVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user, created = auth_services.verify_phone_login(**ser.validated_data)
        return Response(_tokens(user, request, is_new=created))


class MePhoneRequestCodeView(_CodeView):
    """Akkauntga telefon ulash / almashtirish: yangi raqamning Telegram'iga kod."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PhoneSerializer, responses={200: dict})
    def post(self, request):
        ser = PhoneSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        auth_services.request_phone_change(request.user, ser.validated_data["phone"])
        return Response(
            {"detail": TELEGRAM_SENT, "phone": ser.validated_data["phone"], "channel": "telegram"}
        )


class MePhoneVerifyView(_CodeView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PhoneChangeVerifySerializer, responses=UserSerializer)
    def post(self, request):
        ser = PhoneChangeVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = auth_services.verify_phone_change(request.user, **ser.validated_data)
        return Response(UserSerializer(user, context={"request": request}).data)


class PhoneCheckRequestCodeView(_CodeView):
    """Formadagi telefonni tasdiqlash (bron, arizalar, profillar): kod Telegram'ga yuboriladi."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PhoneSerializer, responses={200: dict})
    def post(self, request):
        ser = PhoneSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        auth_services.request_phone_check(ser.validated_data["phone"])
        return Response(
            {"detail": TELEGRAM_SENT, "phone": ser.validated_data["phone"], "channel": "telegram"}
        )


class PhoneCheckVerifyView(_CodeView):
    """Kod to'g'ri bo'lsa — `phone_token`. Formaga telefon bilan birga yuboring (1 soat amal qiladi)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PhoneChangeVerifySerializer, responses=PhoneCheckResponseSerializer)
    def post(self, request):
        ser = PhoneChangeVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone"]
        token = auth_services.verify_phone_check(phone, ser.validated_data["code"], user=request.user)
        return Response({"phone": phone, "phone_token": token})


class GoogleLoginView(_CodeView):
    """Google (Gmail) orqali kirish: Google Identity Services `credential` (ID token) → JWT.
    Akkaunt bo'lmasa avtomatik yaratiladi (`is_new: true`)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=GoogleLoginSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        ser = GoogleLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user, created = google.login(ser.validated_data["credential"])
        return Response(_tokens(user, request, is_new=created))
