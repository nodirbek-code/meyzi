#!/bin/sh
# Render (free plan) uchun API'ni ishga tushirish: migratsiya → statik fayllar → scheduler (fonda) → gunicorn
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py run_scheduler --interval 30 &
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${GUNICORN_WORKERS:-2}" --timeout 120 --access-logfile -
