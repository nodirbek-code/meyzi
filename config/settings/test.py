from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env

# Testlar sukut bo'yicha SQLite'da (tez, Docker'siz). Postgres'da sinash uchun:
# TEST_DATABASE_URL=postgres://... pytest
DATABASES = {
    "default": env.db("TEST_DATABASE_URL", default="sqlite:///:memory:"),
}

SECRET_KEY = "test-only-secret-key-at-least-32-bytes-long"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {"anon": None, "user": None, "auth": None},
}

# Testlar hech qachon haqiqiy Telegram'ga yozmasin (.env da token bo'lsa ham)
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_ADMIN_CHAT_IDS = []
