---
name: meyzi-verify
description: MEYZI backend'ini tekshirish — testlar, ruff, migratsiyalar, deploy check va serverni ishga tushirish. Kod o'zgargandan keyin, "ishlayaptimi", "test qil", "ishga tushir" deyilganda yoki ish tugaganini e'lon qilishdan oldin ishlating.
---

# MEYZI: tekshirish va ishga tushirish

Loyiha: `/mnt/d/meyzi`. Natijani foydalanuvchiga o'zbekcha, qisqa ayting; test yiqilsa — chiqishini ko'rsating.

## Asosiy usul — Docker + Postgres (2026-11-20 dan)

Foydalanuvchi Docker Desktop'ni yoqqan; WSL'dan `docker` ishlaydi. **Doim Docker ichidagi Postgres'dan foydalaning.**

```bash
cd /mnt/d/meyzi
docker compose ps                       # db (healthy), web, scheduler — Up bo'lishi kerak
docker compose up -d                    # o'chiq bo'lsa
```

`web` kodni jonli ulaydi (`.:/app`), o'zgarish darhol qo'llanadi. `web` yiqilsa (masalan, yangi ilovaning
`urls.py` hali yo'q) — `docker compose logs web --tail 30`, tuzatib `docker compose up -d web`.
`web` ishlamayotganda buyruq kerak bo'lsa: `docker compose run --rm -T web <buyruq>`.

## Tekshiruvlar (shu tartibda)

```bash
cd /mnt/d/meyzi
docker compose exec -T web python manage.py makemigrations <app>        # model o'zgargan bo'lsa; faylni o'qing
docker compose exec -T -e TEST_DATABASE_URL=postgres://meyzi:meyzi@db:5432/meyzi web sh -c '
  pytest 2>&1 | tail -3
  ruff format . | tail -1
  ruff check --fix .
  python manage.py makemigrations --check --dry-run --settings=config.settings.test
  python manage.py spectacular --file /dev/null --settings=config.settings.test 2>&1 | grep -iE "warn|error"
'
```

Kutilgan natija: hammasi passed, `All checks passed!`, `No changes detected`, spectacular — bo'sh.
`pytest.ini` da `--ds=config.settings.test` bor — konteynerdagi dev sozlamalari testga ta'sir qilmaydi.
Postgres testi ~1 daqiqa oladi; tez takrorlash uchun bitta faylni SQLite'da: `docker compose exec -T web pytest tests/test_x.py`.

Prod sozlamalari (kutilgan yagona ogohlantirish: `security.W021` HSTS preload):

```bash
docker compose exec -T -e DJANGO_SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(50))") \
  web python manage.py check --deploy --settings=config.settings.prod
```

## Zaxira: Docker'siz (scratchpad venv + SQLite)

Docker ishlamasa: venv'ni loyiha ichida emas, scratchpad'da yarating (`D:\meyzi\.venv` Windows venv bilan to'qnashadi):

```bash
V=<scratchpad>/venv
[ -x $V/bin/python ] || { python3 -m venv $V && $V/bin/pip install -q -r /mnt/d/meyzi/requirements/dev.txt; }
cd /mnt/d/meyzi && $V/bin/pytest && $V/bin/ruff check .
find . -name __pycache__ -prune -exec rm -rf {} +
```

## Jonli serverda sinash (localhost:8000)

```bash
docker compose exec -T web python manage.py seed_tours
B=localhost:8000/api/v1
curl -s $B/tours/ | head -c 400
# login → token → bron → admin servisi orqali tasdiqlash:
docker compose exec -T web python manage.py shell -c "from apps.bookings.services import confirm_booking; ..."
docker compose logs scheduler --tail 3      # "expired: N, completed: M" har daqiqada
```

Dev bazada sinov foydalanuvchilarini qoldirsangiz, foydalanuvchiga ayting.

## Production stack'ni sinash (kerak bo'lganda)

Alohida loyiha nomi va port bilan — dev bazaga tegmaydi. Env faylni scratchpad'da yarating
(`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`, `DJANGO_SECURE_SSL_REDIRECT=False`,
`POSTGRES_PASSWORD`, `NGINX_PORT=8088`):

```bash
export PROD_ENV_FILE=<scratchpad>/prodtest.env
docker compose -p meyzi-prodtest -f docker-compose.prod.yml --env-file $PROD_ENV_FILE up -d --build
# birinchi ishga tushishda migratsiyalar bir necha daqiqa — /api/health/ 200 bo'lguncha kuting
curl localhost:8088/api/health/ ; curl -o /dev/null -w "%{http_code}" localhost:8088/static/admin/css/base.css
docker compose -p meyzi-prodtest -f docker-compose.prod.yml --env-file $PROD_ENV_FILE down -v
rm -rf backups   # sinov dump'lari
```

Shell eslatmasi: `cat > fayl` ni heredoc'siz yozmang (stdin kutib osilib qoladi); uzoq `docker compose exec`
buyruqlariga `timeout N ... </dev/null` qo'shing.

## Hisobot

Faqat haqiqatan bajarilgan narsani ayting: "N ta test o'tdi", "ruff toza", "Postgres'da sinalmadi — Docker o'chiq".
