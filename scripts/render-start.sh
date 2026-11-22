#!/bin/sh
# Render (free plan) uchun API'ni ishga tushirish: migratsiya → statik fayllar → (demo/admin) → scheduler (fonda) → gunicorn
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Demo ma'lumotlar (qayta ishga tushirish xavfsiz). Haqiqiy ishga tushirishda SEED_DEMO=False qiling.
if [ "${SEED_DEMO:-False}" = "True" ]; then
  python manage.py seed_catalog
  python manage.py seed_demo
fi

# Admin: DJANGO_SUPERUSER_EMAIL va DJANGO_SUPERUSER_PASSWORD berilsa yaratiladi (bor bo'lsa — o'tkazib yuboriladi)
if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py createsuperuser --noinput 2>/dev/null || echo "superuser allaqachon bor"
fi

# Telegram bot: token va secret bo'lsa webhook'ni shu serverga o'rnatadi (xato bo'lsa ham server ishga tushaveradi)
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_WEBHOOK_SECRET:-}" ] && [ -n "${MEYZI_SITE_URL:-}" ]; then
  python manage.py telegram_bot --set-webhook "${MEYZI_SITE_URL%/}/api/v1/auth/telegram/webhook/" || echo "Telegram webhook o'rnatilmadi"
fi

python manage.py run_scheduler --interval 30 &
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-2}" --timeout 120 --access-logfile -
