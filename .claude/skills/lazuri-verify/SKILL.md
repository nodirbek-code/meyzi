---
name: lazuri-verify
description: LAZURI backend'ini tekshirish — testlar, ruff, migratsiyalar, deploy check va serverni ishga tushirish. Kod o'zgargandan keyin, "ishlayaptimi", "test qil", "ishga tushir" deyilganda yoki ish tugaganini e'lon qilishdan oldin ishlating.
---

# LAZURI: tekshirish va ishga tushirish

Loyiha: `/mnt/d/lazuri`. Natijani foydalanuvchiga o'zbekcha, qisqa ayting; test yiqilsa — chiqishini ko'rsating.

## Asosiy usul — Docker + Postgres (2026-11-20 dan)

Foydalanuvchi Docker Desktop'ni yoqqan; WSL'dan `docker` ishlaydi. **Doim Docker ichidagi Postgres'dan foydalaning.**

```bash
cd /mnt/d/lazuri
docker compose ps                       # db (healthy), web, scheduler — Up bo'lishi kerak
docker compose up -d                    # o'chiq bo'lsa
```

`web` kodni jonli ulaydi (`.:/app`), o'zgarish darhol qo'llanadi. `web` yiqilsa (masalan, yangi ilovaning
`urls.py` hali yo'q) — `docker compose logs web --tail 30`, tuzatib `docker compose up -d web`.
`web` ishlamayotganda buyruq kerak bo'lsa: `docker compose run --rm -T web <buyruq>`.

## Tekshiruvlar (shu tartibda)

```bash
cd /mnt/d/lazuri
docker compose exec -T web python manage.py makemigrations <app>        # model o'zgargan bo'lsa; faylni o'qing
docker compose exec -T -e TEST_DATABASE_URL=postgres://lazuri:lazuri@db:5432/lazuri web sh -c '
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

Docker ishlamasa: venv'ni loyiha ichida emas, scratchpad'da yarating (`D:\lazuri\.venv` Windows venv bilan to'qnashadi):

```bash
V=<scratchpad>/venv
[ -x $V/bin/python ] || { python3 -m venv $V && $V/bin/pip install -q -r /mnt/d/lazuri/requirements/dev.txt; }
cd /mnt/d/lazuri && $V/bin/pytest && $V/bin/ruff check .
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

## Hisobot

Faqat haqiqatan bajarilgan narsani ayting: "N ta test o'tdi", "ruff toza", "Postgres'da sinalmadi — Docker o'chiq".
