import hmac
import json

from django.conf import settings
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

from . import auth_services, google, telegram_bot
from .serializers import (
    AuthResponseSerializer,
    ChangePasswordSerializer,
    CodeSerializer,
    EmailCodeSerializer,
    EmailSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    PhoneChangeVerifySerializer,
    PhoneCheckResponseSerializer,
    PhoneLoginSerializer,
    PhoneSerializer,
    PhoneVerifySerializer,
    RegisterSerializer,
    TelegramLoginSerializer,
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


class MeEmailRequestCodeView(_CodeView):
    """Profilga email ulash: shu emailga 6 xonali kod yuboriladi."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=EmailSerializer, responses={200: dict})
    def post(self, request):
        ser = EmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        auth_services.request_email_attach(request.user, ser.validated_data["email"])
        return Response(
            {"detail": "Tasdiqlash kodi emailingizga yuborildi.", "email": ser.validated_data["email"]}
        )


class MeEmailVerifyView(_CodeView):
    """Kod to'g'ri bo'lsa — email akkauntga tasdiqlangan holda ulanadi."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=EmailCodeSerializer, responses=UserSerializer)
    def post(self, request):
        ser = EmailCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = auth_services.verify_email_attach(request.user, **ser.validated_data)
        return Response(UserSerializer(user, context={"request": request}).data)


TELEGRAM_SENT = "Tasdiqlash kodi Telegram'ga yuborildi."


class PhoneLoginView(_CodeView):
    """Telefon raqam + parol bilan kirish (parol Telegram bot orqali ro'yxatdan o'tishda o'rnatiladi)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PhoneLoginSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        ser = PhoneLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = auth_services.login_with_phone_password(**ser.validated_data)
        return Response(_tokens(user, request))


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


class TelegramLoginView(_CodeView):
    """Telegram bot yuborgan bir martalik havola (`code`) → JWT. Havola bir marta ishlaydi.
    Bot orqali yangi ro'yxatdan o'tganlar uchun `is_new: true`."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=TelegramLoginSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        ser = TelegramLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user, created = telegram_bot.exchange_login_link(ser.validated_data["code"])
        return Response(_tokens(user, request, is_new=created))


class TelegramPhoneLinkView(APIView):
    """Kirgan foydalanuvchi (masalan Google orqali) uchun "Telefon raqam qo'shish" bot havolasi.

    Bot havoladagi bir martalik token orqali foydalanuvchini taniydi va faqat telefon raqamini so'raydi
    (Telegram kontakti — raqam shu Telegram akkauntiniki ekanini Telegram kafolatlaydi).
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_USERNAME):
            return Response(
                {"detail": "Telegram bot hozircha sozlanmagan."}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        if request.user.phone:
            return Response(
                {"detail": "Akkauntingizda telefon raqam allaqachon bor."}, status=status.HTTP_400_BAD_REQUEST
            )
        token = telegram_bot.issue_phone_link(request.user)
        return Response(
            {
                "url": telegram_bot.phone_link_url(token),
                "expires_in": settings.MEYZI_TELEGRAM_LOGIN_TTL_MINUTES * 60,
            }
        )


@extend_schema(exclude=True)
class TelegramWebhookView(APIView):
    """Telegram Bot API webhook (prod). Telegram `X-Telegram-Bot-Api-Secret-Token` sarlavhasini yuboradi —
    u `TELEGRAM_WEBHOOK_SECRET` ga teng bo'lmasa so'rov rad etiladi."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes: list = []

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        given = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secret or not hmac.compare_digest(given.encode(), secret.encode()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            update = json.loads(request.body or b"{}")
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if isinstance(update, dict):
            telegram_bot.process_update(update)
        # Doim 200: aks holda Telegram shu yangilanishni qayta-qayta yuboradi
        return Response({"ok": True})
