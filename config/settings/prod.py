from .base import *  # noqa: F403
from .base import env

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")  # prod'da majburiy

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]  # konteyner ichidagi healthcheck HTTP orqali
ALLOWED_HOSTS = [*ALLOWED_HOSTS, "localhost"]  # noqa: F405 — healthcheck uchun
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Render: o'z domenini RENDER_EXTERNAL_HOSTNAME orqali beradi
RENDER_EXTERNAL_HOSTNAME = env.str("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# nginx bo'lmagan hostingda media'ni Django beradi
SERVE_MEDIA = env.bool("SERVE_MEDIA", default=False)

# Render free: disk vaqtinchalik (qayta ishga tushganda media/ tozalanadi) — fayllar Cloudinary'da
if CLOUDINARY_URL:  # noqa: F405
    STORAGES = {**STORAGES, "default": {"BACKEND": "apps.core.cloud_storage.CloudinaryStorage"}}  # noqa: F405
    SERVE_MEDIA = False

# Xatolarni kuzatish (ixtiyoriy): SENTRY_DSN berilsa yoqiladi
SENTRY_DSN = env.str("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env.str("SENTRY_ENVIRONMENT", default="production"),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,  # foydalanuvchi shaxsiy ma'lumotlari Sentry'ga yuborilmaydi
    )
