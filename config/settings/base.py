"""LAZURI — umumiy sozlamalar. Muhitga xos sozlamalar dev.py / test.py / prod.py da."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-insecure-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
]
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.agencies",
    "apps.tours",
    "apps.bookings",
    "apps.payments",
    "apps.reviews",
    "apps.content",
    "apps.notifications",
    "apps.guides",
    "apps.hotels",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": env.db("DATABASE_URL", default="postgres://lazuri:lazuri@localhost:5432/lazuri")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
# Platforma tillari: boshlanishiga o'zbek, rus, ingliz. Kontent tarjimasi hali yoqilmagan ("Tez kunda").
LANGUAGES = [
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
# Yopiq fayllar (gid sertifikatlari va h.k.) — veb orqali berilmaydi, faqat admin yuklab oladi
PRIVATE_MEDIA_ROOT = env.path("PRIVATE_MEDIA_ROOT", default=BASE_DIR / "private_media")
# Katta video yuklash uchun (nginx'da ham client_max_body_size)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/min",
        "user": "300/min",
        "auth": "10/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "LAZURI API",
    "DESCRIPTION": "Discover the Blue Road — O'zbekiston turizm platformasi",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "AgencyStatusEnum": "apps.agencies.models.Agency.Status",
        "AgencyApplicationStatusEnum": "apps.agencies.models.AgencyApplication.Status",
        "TourStatusEnum": "apps.tours.models.Tour.Status",
        "DepartureStatusEnum": "apps.tours.models.Departure.Status",
        # tur va mehmonxona bronlari holatlari bir xil
        "BookingStatusEnum": "apps.bookings.models.Booking.Status",
        "BookingCancelledByEnum": "apps.bookings.models.Booking.CancelledBy",
        "UserLanguageEnum": "apps.accounts.models.User.Language",
        "TourMediaKindEnum": "apps.tours.models.TourMedia.Kind",
        "ReviewStatusEnum": "apps.reviews.models.Review.Status",
        "ArticleStatusEnum": "apps.content.models.Article.Status",
        # gid profili va mehmonxona holatlari bir xil (pending/approved/rejected/suspended)
        "PartnerStatusEnum": "apps.guides.models.GuideProfile.Status",
        "GuideBookingStatusEnum": "apps.guides.models.GuideBooking.Status",
        "GuideBookingCancelledByEnum": "apps.guides.models.GuideBooking.CancelledBy",
        "SpokenLanguageEnum": "apps.guides.models.SpokenLanguage",
        "HotelKindEnum": "apps.hotels.models.Hotel.Kind",
        "HotelBookingCancelledByEnum": "apps.hotels.models.HotelBooking.CancelledBy",
    },
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# --- LAZURI biznes parametrlari ---
# Agentlik uchun sukut bo'yicha komissiya (%). Har bir agentlikda alohida o'zgartiriladi.
LAZURI_DEFAULT_COMMISSION_PERCENT = Decimal(env.str("LAZURI_DEFAULT_COMMISSION_PERCENT", default="15"))
# Muddatli to'lov (Uzum Nasiya kabi): jami = narx x ustama, oylik = jami / oylar
LAZURI_INSTALLMENT_MARKUP = Decimal(env.str("LAZURI_INSTALLMENT_MARKUP", default="1.44"))
LAZURI_INSTALLMENT_MONTHS = env.int("LAZURI_INSTALLMENT_MONTHS", default=12)
# Bron: to'lov uchun joylar shuncha daqiqaga band qilinadi
LAZURI_BOOKING_HOLD_MINUTES = env.int("LAZURI_BOOKING_HOLD_MINUTES", default=30)
# Bitta foydalanuvchida bir vaqtda to'lanmagan bronlar soni chegarasi
LAZURI_MAX_PENDING_BOOKINGS = env.int("LAZURI_MAX_PENDING_BOOKINGS", default=3)

# --- Individual gidlar (taqdimot qoidalari) ---
LAZURI_GUIDE_COMMISSION_PERCENT = Decimal(env.str("LAZURI_GUIDE_COMMISSION_PERCENT", default="15"))
LAZURI_GUIDE_RESPONSE_HOURS = env.int("LAZURI_GUIDE_RESPONSE_HOURS", default=24)  # gid javob berish muddati
LAZURI_GUIDE_GROUP_THRESHOLD = env.int(
    "LAZURI_GUIDE_GROUP_THRESHOLD", default=5
)  # shundan katta guruh — ustama

# --- Mehmonxonalar ---
LAZURI_HOTEL_COMMISSION_PERCENT = Decimal(env.str("LAZURI_HOTEL_COMMISSION_PERCENT", default="15"))

# --- Email va SMS (foydalanuvchilarga) ---
# EMAIL_URL misollari: consolemail://  |  smtp+tls://user:parol@smtp.gmail.com:587
vars().update(env.email_url("EMAIL_URL", default="consolemail://"))
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="LAZURI <no-reply@lazuri.uz>")
# console | disabled  (provayder ulanganda — uning nomi)
SMS_BACKEND = env.str("SMS_BACKEND", default="console")
# Tasdiqlash kodi
LAZURI_OTP_TTL_MINUTES = env.int("LAZURI_OTP_TTL_MINUTES", default=10)
LAZURI_OTP_MAX_ATTEMPTS = 5
LAZURI_OTP_RESEND_SECONDS = 60
LAZURI_OTP_MAX_PER_HOUR = 5

# --- Telegram bildirishnomalari (faqat adminlar uchun) ---
# Bo'sh bo'lsa — o'chiq. Sozlash: README → "Telegram bildirishnomalari".
TELEGRAM_BOT_TOKEN = env.str("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_ADMIN_CHAT_IDS = env.list("TELEGRAM_ADMIN_CHAT_IDS", default=[])
# Xabardagi admin panel havolalari uchun
LAZURI_SITE_URL = env.str("LAZURI_SITE_URL", default="http://localhost:8000")

# --- Loglar (stdout — docker logs) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": env.str("LOG_LEVEL", default="INFO")},
    "loggers": {"django.db.backends": {"level": "WARNING"}},
}
