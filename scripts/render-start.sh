#!/bin/sh
# Render (free plan) uchun API'ni ishga tushirish: migratsiya → statik fayllar → (demo/admin) → scheduler (fonda) → gunicorn
set -e

# Diagnostika: qaysi sozlamalar serverga yetib kelgan (qiymatlar chiqarilmaydi)
for v in CLOUDINARY_URL GOOGLE_CLIENT_ID TELEGRAM_BOT_TOKEN TELEGRAM_BOT_USERNAME TELEGRAM_WEBHOOK_SECRET MEYZI_SITE_URL MEYZI_FRONTEND_URL; do
  eval "val=\${$v:-}"
  if [ -n "$val" ]; then echo "[env] $v: BOR"; else echo "[env] $v: YO'Q"; fi
done
# Fayllar qayerda saqlanadi (Cloudinary bo'lmasa — har deploy/qayta ishga tushishda o'chadi)
python manage.py shell -c "from django.core.files.storage import storages; n = type(storages['default']).__name__; print('[storage]', n, '- OK: fayllar Cloudinary da saqlanadi' if n == 'CloudinaryStorage' else '- DIQQAT: server diski, fayllar har deploy da yoqoladi. CLOUDINARY_URL ni meyzi-api Environment ga kiriting')" || echo "[storage] tekshirib bo'lmadi"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Demo ma'lumotlar (qayta ishga tushirish xavfsiz). Haqiqiy ishga tushirishda SEED_DEMO=False qiling.
if [ "${SEED_DEMO:-False}" = "True" ]; then
  python manage.py seed_catalog
  python manage.py seed_demo
fi

# Admin: DJANGO_SUPERUSER_EMAIL dagi foydalanuvchi admin qilinadi (yo'q bo'lsa yaratiladi), parol — Environment'dan
python manage.py ensure_admin || echo "ensure_admin: xato (yuqoridagi xabarni qarang)"

# Platforma yozuvlari bron qilinadigan bo'lsin: turlarga haftaning barcha kunlariga sanalar (120 kun oldinga),
# xonasiz mehmonxonalarga xona turlari, uchrashuv joyisiz gidlarga joy. Faqat yo'q narsani qo'shadi.
python manage.py fill_inventory || echo "fill_inventory: xato"

# Telegram bot: token va secret bo'lsa webhook'ni shu serverga o'rnatadi (xato bo'lsa ham server ishga tushaveradi)
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_WEBHOOK_SECRET:-}" ] && [ -n "${MEYZI_SITE_URL:-}" ]; then
  python manage.py telegram_bot --set-webhook "${MEYZI_SITE_URL%/}/api/v1/auth/telegram/webhook/" || echo "Telegram webhook o'rnatilmadi"
fi

python manage.py run_scheduler --interval 30 &
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-2}" --timeout 120 --access-logfile -
