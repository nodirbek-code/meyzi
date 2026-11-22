# LAZURI — Discover the Blue Road

**LAZURI** — O'zbekiston bo'ylab turlar platformasi (backend — Django/DRF, frontend — Next.js). Tekshirilgan turagentliklar turlarini joylaydi,
turist sana va joyni tanlab, onlayn to'laydi (karta yoki muddatli to'lov). **LAZURI'ning o'zi ham** tur yaratadi —
platforma faqat agregator emas. Ushbu repozitoriy — platformaning **backend (REST API)** qismi.

> Ishlash modeli: [triphub.uz](https://www.triphub.uz/) (agentlik → tur → jo'nash sanasi → bron → to'lov).
> Qo'shimcha g'oyalar (individual gidlar, mehmonxonalar, AI marshrut): `D:\proyekt\LAZURI.pptx`.

---

## Mundarija

1. [Texnologiyalar](#texnologiyalar)
2. [Talablar](#talablar)
3. [Tez boshlash (Docker)](#tez-boshlash-docker)
4. [Lokal ishga tushirish (venv)](#lokal-ishga-tushirish-venv)
5. [Muhit o'zgaruvchilari (.env)](#muhit-ozgaruvchilari-env)
6. [Foydali buyruqlar](#foydali-buyruqlar)
7. [Testlar va kod sifati](#testlar-va-kod-sifati)
8. [Loyiha tuzilmasi](#loyiha-tuzilmasi)
9. [API](#api)
10. [Rollar va ruxsatlar](#rollar-va-ruxsatlar)
11. [Biznes qoidalari](#biznes-qoidalari)
12. [Yo'l xaritasi](#yol-xaritasi)
13. [Muammolar va yechimlar](#muammolar-va-yechimlar)

---

## Texnologiyalar

| Qatlam | Texnologiya |
|---|---|
| Til | Python 3.12+ |
| Framework | Django 5.2 (LTS), Django REST Framework 3.16+ |
| Ma'lumotlar bazasi | PostgreSQL 16 (testlarda — SQLite) |
| Autentifikatsiya | JWT — `djangorestframework-simplejwt` (refresh rotatsiya + blacklist) |
| Parol xeshlash | Argon2 |
| API hujjatlari | OpenAPI 3 / Swagger — `drf-spectacular` |
| Filtrlash | `django-filter`, DRF Search/Ordering |
| Konfiguratsiya | `django-environ` (`.env` fayl) |
| Server | Gunicorn (prod), `runserver` (dev) |
| Konteyner | Docker, Docker Compose |
| Testlar / lint | pytest + pytest-django, ruff |

## Talablar

- **Docker usuli uchun:** Docker Desktop (Compose v2.24+).
- **Lokal usul uchun:** Python 3.12+ va ishlab turgan PostgreSQL.
- Git.

> **WSL foydalanuvchilari:** `docker` buyrug'i WSL ichida topilmasa, Docker Desktop'da
> *Settings → Resources → WSL Integration* bo'limida distributivingizni yoqing.

## Tez boshlash (Docker)

```bash
cd D:\lazuri                 # WSL'da: cd /mnt/d/lazuri
cp .env.example .env         # Windows CMD'da: copy .env.example .env
docker compose up --build
```

Bu buyruq uchta konteyner ko'taradi:

- `db` — PostgreSQL 16 (`localhost:5432`, baza/foydalanuvchi/parol: `lazuri`);
- `web` — Django, avval `migrate` bajaradi, so'ng `http://localhost:8000` da ishga tushadi
  (kod papkasi konteynerga ulangan — o'zgarishlar darhol qo'llanadi);
- `frontend` — Next.js (dev) `http://localhost:3000` — sayt shu yerda;
- `scheduler` — har 15 soniyada: `process_bookings` (to'lanmagan bronlarning joyini bo'shatadi, tugagan
  sayohatlarni yopadi) va `send_notifications` (adminlarga Telegram xabarlari).

Ikkinchi terminalda admin yarating va demo ma'lumot yuklang:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo       # hammasi: turlar, FAQ, 2 gid, 2 mehmonxona
```

Tayyor:

| Manzil | Nima |
|---|---|
| http://localhost:8000/api/docs/ | Swagger — barcha endpoint'lar, shu yerdan sinab ko'rish mumkin |
| http://localhost:8000/api/schema/ | OpenAPI sxema (YAML) |
| http://localhost:8000/admin/ | Django admin panel |

To'xtatish: `docker compose down` (ma'lumotlar `pgdata` volume'da saqlanib qoladi;
butunlay o'chirish uchun `docker compose down -v`).

## Lokal ishga tushirish (venv)

PostgreSQL kerak. Eng osoni — faqat bazani Docker'da ko'tarish: `docker compose up -d db`.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
cp .env.example .env                 # DATABASE_URL localhost'ga qaraydi
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_tours
python manage.py runserver
```

`manage.py` sukut bo'yicha `config.settings.dev` sozlamalaridan foydalanadi.

## Muhit o'zgaruvchilari (.env)

| O'zgaruvchi | Sukut bo'yicha | Izoh |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev uchun vaqtinchalik kalit | **Prod'da majburiy**, uzun tasodifiy satr |
| `DJANGO_DEBUG` | `False` | `dev` sozlamalari baribir `True` qiladi |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Vergul bilan ajratiladi |
| `DATABASE_URL` | `postgres://lazuri:lazuri@localhost:5432/lazuri` | Docker'da `web` uchun avtomatik `db:5432` |
| `JWT_ACCESS_MINUTES` | `30` | Access token muddati (daqiqa) |
| `JWT_REFRESH_DAYS` | `30` | Refresh token muddati (kun) |
| `CORS_ALLOWED_ORIGINS` | bo'sh | Frontend manzillari; `dev` da hamma manzilga ruxsat |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` | Faqat `prod` — HTTPS'ga yo'naltirish |
| `TEST_DATABASE_URL` | `sqlite:///:memory:` | Faqat testlar — Postgres'da sinash uchun |
| `LAZURI_DEFAULT_COMMISSION_PERCENT` | `15` | Yangi agentlik uchun LAZURI komissiyasi (%), keyin har biriga alohida |
| `LAZURI_INSTALLMENT_MARKUP` | `1.44` | Muddatli to'lov ustamasi: jami = narx × 1.44 |
| `LAZURI_INSTALLMENT_MONTHS` | `12` | Muddatli to'lov oylari: oylik = jami ÷ 12 |
| `LAZURI_BOOKING_HOLD_MINUTES` | `30` | To'lov uchun joylar shuncha daqiqa band turadi |
| `LAZURI_MAX_PENDING_BOOKINGS` | `3` | Bitta foydalanuvchida bir vaqtda to'lanmagan bronlar chegarasi |
| `LAZURI_GUIDE_COMMISSION_PERCENT` | `15` | Individual gid bronidan LAZURI ulushi (gid — 85%) |
| `LAZURI_GUIDE_RESPONSE_HOURS` | `24` | Gid so'rovga javob berish muddati |
| `LAZURI_GUIDE_GROUP_THRESHOLD` | `5` | Shu va undan katta guruhga gid ustamasi (sukut +20%) |
| `LAZURI_HOTEL_COMMISSION_PERCENT` | `15` | Yangi mehmonxona uchun komissiya (har biriga alohida o'zgartiriladi) |
| `TELEGRAM_BOT_TOKEN` | bo'sh | Admin bildirishnomalari uchun bot tokeni (@BotFather). Bo'sh — o'chiq |
| `TELEGRAM_ADMIN_CHAT_IDS` | bo'sh | Xabar oladigan admin chatlari, vergul bilan |
| `LAZURI_SITE_URL` | `http://localhost:8000` | Telegram xabaridagi admin panel havolalari uchun |
| `EMAIL_URL` | `consolemail://` | Email: konsol (dev) yoki `smtp+tls://login:parol@smtp.server:587` |
| `DEFAULT_FROM_EMAIL` | `LAZURI <no-reply@lazuri.uz>` | Jo'natuvchi |
| `SMS_BACKEND` | `console` | `console` (kod server logida) / `disabled`. Provayder (Eskiz, Playmobile) shartnomadan keyin ulanadi |
| `PRIVATE_MEDIA_ROOT` | `private_media/` | Yopiq fayllar (gid sertifikatlari) — veb orqali berilmaydi |
| `SENTRY_DSN` | bo'sh | Xatolarni kuzatish (faqat prod) |
| `CSRF_TRUSTED_ORIGINS` | bo'sh | Prod: `https://api.lazuri.uz` |

Kalit yaratish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Sozlamalar fayllari

| Fayl | Qachon |
|---|---|
| `config/settings/base.py` | Umumiy sozlamalar |
| `config/settings/dev.py` | Ishlab chiqish: DEBUG, barcha hostlar, email konsolga |
| `config/settings/test.py` | pytest: SQLite, tez xeshlash, throttling o'chiq |
| `config/settings/prod.py` | Production: HTTPS, xavfsiz cookie, HSTS. `wsgi.py`/`asgi.py` sukut bo'yicha shuni ishlatadi |

## Frontend (Next.js)

`frontend/` — Next.js 15 (App Router) + TypeScript + Tailwind CSS. Tuzilish va foydalanuvchi yo'li — triphub.uz kabi,
dizayn — LAZURI'ning o'zi: **lazurit ko'k** `#1E3A8A`, **oltin** `#C9A227`, qum fon `#F7F3EA`, girih naqshi,
sarlavhalar Playfair Display, matn Inter (kirill ham bor).

| Sahifa | Yo'l |
|---|---|
| Bosh sahifa: qidiruv, toifalar, mashhur turlar, yo'nalishlar, LAZURI turlari, "Tez kunda" | `/` |
| Turlar (filtrlar, sahifalash) · tur sahifasi (galereya, dastur, sanalar, bron) | `/tours` · `/tours/[slug]` |
| Yo'nalishlar · yo'nalish (turlar, diqqatga sazovor joylar) | `/destinations` · `/destinations/[slug]` |
| Gidlar · gid (narx kalkulyatori, so'rov) · gid bo'lish | `/guides` · `/guides/[slug]` · `/guides/become` |
| Mehmonxonalar (sana bo'yicha) · mehmonxona (bo'sh xonalar, bron) · qo'shish | `/hotels` · `/hotels/[slug]` · `/hotels/join` |
| Kirish (telefon+SMS / email) · ro'yxatdan o'tish · parolni tiklash | `/login` · `/register` · `/forgot-password` |
| Kabinet: bronlarim, bron (taymer, bekor qilish, sharh), profil | `/account` · `/account/bookings/[code]` · `/account/profile` |
| Qo'llanmalar · FAQ · sahifalar · agentliklar uchun | `/articles` · `/faq` · `/pages/[slug]` · `/agencies` |

**Xavfsizlik:** JWT'lar faqat **httpOnly cookie**'da (`lz_access`, `lz_refresh`) — brauzer JavaScript'i ko'rmaydi.
Brauzer backendga to'g'ridan emas, `/api/proxy/...` (Next route handler) orqali murojaat qiladi; kirish/chiqish —
`/api/auth/*`. Access token muddati tugashidan oldin `middleware.ts` uni jimgina yangilaydi.
Server Component'lar backendni ichki manzil (`API_INTERNAL_URL=http://web:8000`) orqali o'qiydi.

```bash
docker compose up -d frontend                          # dev (birinchi marta npm install — bir necha daqiqa)
docker compose exec frontend npx tsc --noEmit         # tip tekshiruvi
docker compose exec frontend npm run build            # prod build tekshiruvi
```

Hali yo'q (keyingi bosqich): agentlik, gid va mehmonxona **kabinetlari** frontend'i (backend API tayyor).

## Foydali buyruqlar

```bash
python manage.py makemigrations          # model o'zgargach
python manage.py migrate
python manage.py seed_catalog            # demo shaharlar va joylar (qayta ishga tushirish xavfsiz)
python manage.py seed_tours              # seed_catalog + toifalar, LAZURI agentligi, 3 ta tur, sanalar
python manage.py process_bookings        # muddati o'tgan bronlar → expired, tugaganlar → completed
python manage.py seed_content            # FAQ (qayta ishga tushirish xavfsiz)
python manage.py seed_demo               # seed_tours + seed_content + 2 demo gid + 2 demo mehmonxona
python manage.py send_notifications      # navbatdagi Telegram xabarlarini yuborish
python manage.py telegram_chat_ids       # botga /start yozgan chatlar ID'si
python manage.py telegram_test           # adminlarga sinov xabari
python manage.py createsuperuser
python manage.py spectacular --file schema.yml   # OpenAPI sxemani faylga
```

Docker'da har birining oldiga `docker compose exec web` qo'shing.

- `seed_catalog` — 4 ta shahar (Toshkent, Samarqand, Buxoro, Xiva) va 12 ta joy. Koordinatalar taxminiy,
  kirish narxlari **namunaviy** — real narxlarni admin panel orqali yangilang.
- `seed_tours` — yuqoridagilar + Chimyon, Zomin, Chorvoq; 4 ta toifa (Tog', Madaniy, Sarguzasht, Dam olish kuni);
  **LAZURI** agentligi (platformaning o'zi, komissiyasiz, moderatsiyasiz); 3 ta tur kunlik dasturi bilan va
  kelgusi 6 ta shanbaga jo'nash sanalari (20 joydan). Turlarda rasm yo'q — kabinet yoki admin orqali yuklang.

## Testlar va kod sifati

**Asosiy usul — Docker ichida, Postgres bilan** (pytest alohida `test_lazuri` bazasini yaratadi, ish bazasiga tegmaydi):

```bash
docker compose exec -e TEST_DATABASE_URL=postgres://lazuri:lazuri@db:5432/lazuri web pytest
docker compose exec web pytest tests/test_bookings.py     # bitta fayl (SQLite)
docker compose exec web pytest -k cancel                  # nom bo'yicha
docker compose exec web ruff check .                      # lint
docker compose exec web ruff format .                     # formatlash
```

Docker'siz: `pytest` (sukut bo'yicha SQLite, xotirada). `pytest.ini` doim `config.settings.test` ni ishlatadi
(`--ds`), shuning uchun konteynerdagi `DJANGO_SETTINGS_MODULE=...dev` testlarga ta'sir qilmaydi.

Production sozlamalarini tekshirish:

```bash
DJANGO_SECRET_KEY=... python manage.py check --deploy --settings=config.settings.prod
```

## Loyiha tuzilmasi

```
lazuri/
├── config/
│   ├── settings/          base.py · dev.py · test.py · prod.py
│   ├── urls.py            /admin/, /api/v1/, /api/docs/, /api/schema/
│   ├── wsgi.py · asgi.py
├── apps/
│   ├── core/              umumiy kod: TimeStampedModel, StandardPagination, IsAdminOrReadOnly
│   ├── accounts/          User modeli (email login, rollar), JWT auth, profil
│   ├── catalog/           Destination (yo'nalish), Place (joy), PlaceImage, seed_catalog
│   ├── agencies/          Agency, AgencyMember, AgencyApplication (ariza → tekshiruv → faol)
│   ├── tours/             TourCategory, Tour, TourMedia, ItineraryDay/Item, Departure,
│                          pricing.py (muddatli to'lov), policies.py (bekor qilish), kabinet API, seed_tours
│   ├── bookings/          Booking, Traveler; services.py (band qilish, tasdiqlash, bekor qilish), process_bookings
│   ├── payments/          methods.py — to'lov usullari ro'yxati ("Tez kunda"), static/payments/ — logotiplar
│   ├── reviews/           Review; services.py (sharh, reyting hisobi, agentlik javobi)
│   ├── content/           Article (Qo'llanmalar), FaqItem, Page (shartlar, maxfiylik); seed_content
│   ├── notifications/     TelegramMessage (outbox), telegram.py, services.py (hodisalar), buyruqlar
│   ├── guides/            GuideProfile, GuideBooking, GuideReview, band kunlar; policies.py (taqdimot qoidalari)
│   └── hotels/            Hotel, RoomType, HotelBooking, HotelReview; bo'sh xonalar hisobi
├── tests/                 pytest testlari (conftest.py — umumiy fixture'lar)
├── requirements/          base.txt (prod) · dev.txt (+ pytest, ruff)
├── Dockerfile · docker-compose.yml
├── .env.example
├── pytest.ini · ruff.toml
└── manage.py
```

Har bir ilova (`apps/<nom>/`) bir xil tartibda: `models.py` → `serializers.py` → `views.py` → `urls.py`
→ `admin.py`, kerak bo'lsa `filters.py`, `services.py` (biznes mantiq) va `management/commands/`.

## API

Barcha endpoint'lar `/api/v1/` ostida. To'liq va interaktiv ro'yxat — `/api/docs/`.

### Autentifikatsiya

| Metod | Endpoint | Auth | Vazifa |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | — | Ro'yxatdan o'tish → `user` + `access` + `refresh` |
| POST | `/api/v1/auth/login/` | — | Email + parol → `user` + `access` + `refresh` |
| POST | `/api/v1/auth/token/refresh/` | — | Yangi `access` (va yangi `refresh` — rotatsiya) |
| POST | `/api/v1/auth/logout/` | ✅ | `refresh` tokenni bekor qilish (blacklist) |
| GET | `/api/v1/auth/me/` | ✅ | Joriy foydalanuvchi |
| PATCH | `/api/v1/auth/me/` | ✅ | Profilni tahrirlash (`email` va `role` o'zgarmaydi) |
| POST | `/api/v1/auth/me/password/` | ✅ | `old_password` + `new_password` |
| POST | `/api/v1/auth/password/forgot/` | — | `{"email"}` → emailga 6 raqamli kod (javob doim bir xil) |
| POST | `/api/v1/auth/password/reset/` | — | `{"email", "code", "new_password"}` → barcha qurilmalardan chiqariladi |
| POST | `/api/v1/auth/email/send-code/` · `email/verify/` | ✅ | Emailni tasdiqlash (`{"code"}`); ro'yxatdan o'tganda kod avtomatik yuboriladi |
| POST | `/api/v1/auth/phone/request-code/` | — | `{"phone": "90 123 45 67"}` → SMS kod |
| POST | `/api/v1/auth/phone/verify/` | — | `{"phone", "code", "first_name"?}` → tokenlar; akkaunt bo'lmasa yaratiladi (`is_new: true`) |
| POST | `/api/v1/auth/me/phone/request-code/` · `me/phone/verify/` | ✅ | Akkauntga telefon ulash/almashtirish |

**Tasdiqlash kodlari:** 6 raqam, 10 daqiqa amal qiladi, bazada faqat xeshi saqlanadi; 5 ta noto'g'ri urinishdan keyin
kod yaroqsiz; qayta so'rash — 60 soniyadan keyin, bitta manzilga soatiga 5 tagacha. Telefon formati: `+998XXXXXXXXX`
(`90 123 45 67`, `+998 (90) 123-45-67` ham qabul qilinadi). Telefon orqali kirganlar parolsiz, email ixtiyoriy.
`email` va `phone` ni `PATCH /me/` bilan o'zgartirib bo'lmaydi — faqat kod orqali.

So'rovlarda token: `Authorization: Bearer <access>`.

**Misol:**

```bash
# Ro'yxatdan o'tish
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"Kuchli-Parol-2026","first_name":"Ali","role":"tourist","language":"uz"}'

# Kirish
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"Kuchli-Parol-2026"}'

# Profil
curl http://localhost:8000/api/v1/auth/me/ -H "Authorization: Bearer <access>"
```

Javob (`register` / `login`):

```json
{
  "user": {"id": 1, "email": "ali@example.com", "first_name": "Ali", "role": "tourist", "language": "uz", "...": "..."},
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

Ro'yxatdan o'tish maydonlari: `email`, `password` (majburiy); `first_name`, `last_name`, `phone`,
`role` (`tourist` | `guide` | `business`, sukut — `tourist`), `language` (`uz` `ru` `en`),
`country` (ISO 2 harf: `UZ`, `US`...). Email registrga sezgir emas (`Ali@Example.com` = `ali@example.com`).

### Katalog

| Metod | Endpoint | Vazifa |
|---|---|---|
| GET | `/api/v1/catalog/destinations/` | Shaharlar ro'yxati (`places_count` bilan) |
| GET | `/api/v1/catalog/destinations/{slug}/` | Bitta shahar (`description` bilan) |
| GET | `/api/v1/catalog/places/` | Joylar ro'yxati |
| GET | `/api/v1/catalog/places/{slug}/` | Joy batafsil: tarix, manzil, ish vaqti, audio-gid, rasmlar |
| POST / PUT / PATCH / DELETE | yuqoridagilar | Faqat admin |

Obyektlar `id` emas, **`slug`** bo'yicha olinadi: `/places/registon/`.

**Joylar filtrlari** (`/api/v1/catalog/places/`):

| Parametr | Misol | Izoh |
|---|---|---|
| `destination` | `?destination=samarqand` | Shahar slug'i |
| `category` | `?category=museum&category=bazaar` | Bir nechta bo'lishi mumkin |
| `is_free` | `?is_free=true` | Bepul joylar |
| `max_fee` | `?max_fee=50000` | Kirish narxi (so'm) ≤ |
| `is_featured` | `?is_featured=true` | Tavsiya etilganlar |
| `search` | `?search=bozor` | Nom, tavsif, shahar nomi bo'yicha |
| `ordering` | `?ordering=-entry_fee_uzs` | `name`, `entry_fee_uzs`, `visit_duration_minutes`, `created_at` |

**Shaharlar filtrlari:** `is_featured`, `region`, `search`, `ordering` (`name`, `sort_order`).

Toifalar (`category`): `monument`, `mosque`, `museum`, `bazaar`, `nature`, `craft`, `restaurant`, `park`, `other`.

### Turlar (ommaviy)

| Metod | Endpoint | Vazifa |
|---|---|---|
| GET | `/api/v1/tours/` | Turlar katalogi (kartochkalar) |
| GET | `/api/v1/tours/{slug}/` | Tur sahifasi: media, kunlik dastur, kiradi/kirmaydi, uchrashuv joyi, kelgusi sanalar |
| GET | `/api/v1/tours/categories/` | Toifalar (`tours_count` bilan) |

Faqat **e'lon qilingan** turlar, **faol** agentlik va e'lon qilingan yo'nalish bo'yicha ko'rinadi.

**Filtrlar** (`/api/v1/tours/`):

| Parametr | Misol | Izoh |
|---|---|---|
| `search` | `?search=zomin` | Nom, tavsif, yo'nalish, agentlik nomi |
| `destination` | `?destination=zomin` | Yo'nalish slug'i |
| `category` | `?category=tog,madaniy` | Toifa slug'i, vergul bilan bir nechta |
| `agency` | `?agency=lazuri` | Agentlik slug'i |
| `min_price`, `max_price` | `?max_price=1000000` | Narx (so'm, 1 kishi) |
| `min_days`, `max_days` | `?min_days=2` | Davomiylik (kun) |
| `date` | `?date=2026-11-28` | Shu kuni bo'sh joyli jo'nash bor |
| `date_from`, `date_to` | `?date_from=2026-12-01&date_to=2026-12-31` | Oraliqda bo'sh joyli jo'nash bor (bitta sana ikkala shartga mos) |
| `cancellation_policy` | `?cancellation_policy=free` | `free` / `partial` / `non_refundable` |
| `is_featured` | `?is_featured=true` | Mashhur turlar |
| `ordering` | `?ordering=price_uzs` | `price_uzs` (arzondan), `-price_uzs` (qimmatdan), `duration_days`, `-rating`, `-published_at` |

**Kartochka** maydonlari: `title`, `cover`, `categories`, `destination`, `agency`, `duration_days`,
`duration_nights`, `price_uzs`, `installment` (`{"months": 12, "monthly_uzs": 106800, "total_uzs": 1281600}`),
`next_departure` (eng yaqin bo'sh joyli sana: `date`, `seats_left`, `price_uzs`), `cancellation_policy`, `rating`.

### Turagentliklar

| Metod | Endpoint | Kim | Vazifa |
|---|---|---|---|
| GET | `/api/v1/agencies/` | hamma | Faol agentliklar (`tours_count` bilan) |
| GET | `/api/v1/agencies/{slug}/` | hamma | Agentlik sahifasi |
| POST | `/api/v1/agencies/applications/` | hamma | Hamkorlik arizasi: `agency_name`, `contact_person`, `phone` (+ `email`, `message`) |
| GET | `/api/v1/agencies/applications/` | login | Admin — barcha arizalar, foydalanuvchi — o'ziniki |
| POST | `/api/v1/agencies/applications/{id}/approve/` | admin | Agentlik yaratiladi, ariza bergan foydalanuvchi uning egasi bo'ladi |
| POST | `/api/v1/agencies/applications/{id}/reject/` | admin | `{"note": "..."}` |

Arizani login qilgan holda yuboring — shunda tasdiqlangach shu akkaunt agentlik kabinetiga kiradi.

### Agentlik kabineti (`/api/v1/cabinet/`)

Faqat **faol** agentlik xodimlari uchun (boshqalarga — `403`). Har kim faqat o'z agentligi ma'lumotini ko'radi.

| Metod | Endpoint | Vazifa |
|---|---|---|
| GET / PATCH | `/cabinet/agency/` | Agentlik profili (holat, komissiya, tekshiruv — faqat admin o'zgartiradi) |
| GET | `/cabinet/stats/` | Turlar soni holat bo'yicha, kelgusi sanalar, joylar |
| GET / POST | `/cabinet/tours/` | O'z turlari / yangi tur (qoralama) |
| GET / PATCH / DELETE | `/cabinet/tours/{slug}/` | Tahrirlash. `itinerary` yuborilsa — dastur to'liq almashtiriladi |
| POST | `/cabinet/tours/{slug}/submit/` | E'longa yuborish (kamida 1 rasm kerak) |
| POST | `/cabinet/tours/{slug}/archive/` | Arxivlash |
| GET / POST | `/cabinet/tours/{slug}/departures/` | Jo'nash sanalari: `date`, `seats_total`, `price_uzs` (ixtiyoriy), `status` |
| PATCH / DELETE | `/cabinet/tours/{slug}/departures/{id}/` | Band joydan kam qilib bo'lmaydi; bronli sanani o'chirib bo'lmaydi. `status: "cancelled"` — barcha bronlar 100% qaytarish bilan bekor qilinadi |
| GET / POST | `/cabinet/tours/{slug}/media/` | Rasm/video yuklash (`multipart/form-data`: `file`, `kind`, `is_cover`, `caption`) |
| PATCH / DELETE | `/cabinet/tours/{slug}/media/{id}/` | Bitta tur — bitta muqova (`is_cover`) |
| GET | `/cabinet/bookings/` | Agentlik bronlari: `?status=confirmed&tour=<slug>&departure=<id>&search=<kod/ism/tel>` |
| GET | `/cabinet/bookings/{code}/` | Bron: sayohatchilar, kontakt, komissiya va agentlik ulushi |
| POST | `/cabinet/bookings/{code}/cancel/` | Agentlik bekor qiladi — turistga **100%** qaytariladi |

Tur yaratish namunasi:

```json
{
  "title": "Zomin — 2 kun / 1 kecha",
  "destination": "zomin",
  "categories": ["tog"],
  "duration_days": 2, "duration_nights": 1,
  "price_uzs": 890000, "price_note": "2 kishilik xonada 1 kishi uchun",
  "cancellation_policy": "free",
  "departure_time": "06:00", "return_time": "19:30",
  "meeting_point": "Toshkent, Amir Temur xiyoboni",
  "included": ["Transport", "Gid", "3 mahal ovqat"],
  "not_included": ["1-kun tushligi"],
  "what_to_bring": ["Pasport", "Qulay poyabzal"],
  "itinerary": [
    {"day_number": 1, "title": "Tog'larga yo'l", "items": [
      {"start_time": "06:00", "end_time": "06:30", "title": "Yig'ilish"},
      {"start_time": "11:00", "end_time": "12:00", "title": "Tushlik", "is_extra_cost": true}
    ]},
    {"day_number": 2, "title": "Kanyon va qaytish", "items": []}
  ]
}
```

**Tur holatlari:** `draft` (qoralama) → `submit` → `pending_review` (moderatsiya) → admin tasdiqlaydi →
`published`. `auto_publish` yoqilgan agentlik (masalan, LAZURI) uchun `submit` darhol `published` qiladi.
Rad etilsa — `rejected` (`moderation_note` da sabab), tuzatib qayta yuborish mumkin. `archived` — katalogdan olinadi.

### Bronlar (turist)

| Metod | Endpoint | Vazifa |
|---|---|---|
| POST | `/api/v1/bookings/` | Bron qilish → joylar **30 daqiqaga** band (`status: pending_payment`, `expires_at`) |
| GET | `/api/v1/bookings/` | O'z bronlari (`?status=confirmed`) |
| GET | `/api/v1/bookings/{code}/` | Bron (raqami `LZ` bilan boshlanadi, masalan `LZF9FPLFGJ`) |
| GET | `/api/v1/bookings/{code}/cancel-preview/` | Hozir bekor qilsam qancha qaytadi? |
| POST | `/api/v1/bookings/{code}/cancel/` | Bekor qilish (`{"reason": "..."}`) |

Hammasi login talab qiladi. So'rov:

```json
{
  "departure": 13,
  "seats": 2,
  "contact_name": "Ali Valiyev",
  "contact_phone": "+998901234567",
  "contact_email": "ali@example.com",
  "note": "Vegetarian ovqat",
  "travelers": [{"full_name": "Ali Valiyev"}, {"full_name": "Vali Aliyev", "birth_date": "1995-04-01"}]
}
```

`departure` — tur sahifasidagi `departures[].id`. `travelers` ixtiyoriy, berilsa soni `seats` ga teng bo'lishi kerak.

**Bron holatlari:**

| Holat | Ma'nosi | Joy band? |
|---|---|---|
| `pending_payment` | To'lov kutilmoqda, `expires_at` gacha | ✅ |
| `confirmed` | To'langan | ✅ |
| `expired` | 30 daqiqada to'lanmadi — joylar sotuvga qaytdi | — |
| `cancelled` | Bekor qilindi (`cancelled_by`: `tourist` / `agency` / `admin`, `refund_uzs`) | — |
| `completed` | Sayohat tugadi | — |

> To'lov hali ulanmagan. Sinov uchun bronni admin panel → Bronlar → *"To'langan deb belgilash"* bilan tasdiqlash mumkin.

### Imkoniyatlar (frontend uchun)

| Metod | Endpoint | Vazifa |
|---|---|---|
| GET | `/api/v1/features/` | Tillar, AI marshrut, ko'p tilli kontent, to'lov usullari — `enabled` / `status_text` |

```json
{
  "languages": [{"code": "uz", "name": "O'zbekcha"}, {"code": "ru", "name": "Русский"}, {"code": "en", "name": "English"}],
  "default_language": "uz",
  "ai_route": {"enabled": false, "status_text": "Tez kunda", "description": "..."},
  "multilingual_content": {"enabled": false, "status_text": "Tez kunda", "description": "..."},
  "payments": [{"code": "payme", "enabled": false, "status_text": "Tez kunda", "...": "..."}]
}
```

- **AI marshrut** — "Tez kunda", kod yo'q. Gidlar va mehmonxonalar — to'liq ishlaydi (quyida).
- **Tillar** — boshlanishiga 3 ta: o'zbek, rus, ingliz (`User.language`). Kontent tarjimasi hali yo'q (barcha matnlar
  o'zbekcha) — keyin shu 3 til bilan qo'shiladi.

### To'lov usullari

| Metod | Endpoint | Vazifa |
|---|---|---|
| GET | `/api/v1/payments/methods/` | Payme, Click, Uzum Nasiya — hozircha hammasi **"Tez kunda"** (`enabled: false`) |

```json
[{"code": "payme", "name": "Payme", "description": "...", "logo": null, "enabled": false, "status_text": "Tez kunda"}, ...]
```

To'lov kodi yo'q — faqat ko'rinish. Logotiplarni `apps/payments/static/payments/` ga `payme.svg`, `click.svg`,
`uzum_nasiya.svg` (yoki `.png`) nomi bilan qo'ying (rasmiy brend to'plamlaridan) — `logo` da URL paydo bo'ladi.

### Sharhlar

| Metod | Endpoint | Kim | Vazifa |
|---|---|---|---|
| GET | `/api/v1/reviews/` | hamma | E'lon qilingan sharhlar: `?tour=<slug>&agency=<slug>&rating=5` |
| GET / POST | `/api/v1/reviews/my/` | login | O'z sharhlarim / yangi: `{"booking": "LZ...", "rating": 1-5, "text": "..."}` |
| PATCH | `/api/v1/reviews/my/{id}/` | login | Tahrirlash (14 kun ichida) |
| GET | `/api/v1/cabinet/reviews/` | agentlik | Agentlik turlariga sharhlar (yashirilganlari ham) |
| POST | `/api/v1/cabinet/reviews/{id}/reply/` | agentlik | Javob: `{"text": "..."}` (bo'sh — javobni o'chirish) |

- Sharh faqat **yakunlangan** (`completed`) bron egasidan, bitta bronga bitta.
- Tur va agentlikning `rating` / `reviews_count` maydonlari avtomatik qayta hisoblanadi (faqat e'lon qilinganlar).
- Muallif ommaga "Ism F." ko'rinishida chiqadi. Admin sharhni yashira oladi (admin panel → Sharhlar).

### Kontent

| Metod | Endpoint | Vazifa |
|---|---|---|
| GET | `/api/v1/articles/` | Qo'llanmalar (blog): `?destination=<slug>&search=...` |
| GET | `/api/v1/articles/{slug}/` | Maqola + bog'liq turlar kartochkalari |
| GET | `/api/v1/faq/` | Savol-javoblar |
| GET | `/api/v1/pages/{slug}/` | Sahifa: `terms`, `privacy`, `about`... |

Hammasi admin paneldan boshqariladi (*Kontent* bo'limi). Foydalanish shartlari va maxfiylik siyosati —
yuridik matn, admin panelda `terms` va `privacy` slug'lari bilan yarating.

### Individual gidlar

| Metod | Endpoint | Kim | Vazifa |
|---|---|---|---|
| GET | `/api/v1/guides/` | hamma | Tasdiqlangan gidlar: `?destination=&language=en&specialization=history&max_price=&date=` |
| GET | `/api/v1/guides/{slug}/` | hamma | Gid profili |
| GET | `/api/v1/guides/{slug}/quote/` | hamma | Narx: `?duration=half_day\|full_day\|multi_day&days=3&group_size=6` |
| GET | `/api/v1/guides/{slug}/busy-dates/` | hamma | Keyingi 90 kun band kunlari |
| GET | `/api/v1/guides/{slug}/reviews/` | hamma | Sharhlar |
| GET / POST / PATCH | `/api/v1/guides/me/` | login | Gid bo'lish arizasi / profilim (`pending` → admin tasdiqlaydi) |
| POST | `/api/v1/guide-bookings/` | login | So'rov: `guide`, `destination`, `duration`, `start_date`, `start_time`, `days`, `group_size`, `language`, `meeting_point`, kontakt |
| GET | `/api/v1/guide-bookings/` · `{code}/` | login | O'z so'rovlari (raqam `LG...`) |
| GET / POST | `/api/v1/guide-bookings/{code}/cancel-preview/` · `cancel/` | login | Bekor qilish |
| POST | `/api/v1/guide-bookings/{code}/review/` | login | Sharh (yakunlangandan keyin) |
| GET | `/api/v1/cabinet/guide/bookings/` | gid | Kelgan so'rovlar |
| POST | `/api/v1/cabinet/guide/bookings/{code}/accept/` · `decline/` · `cancel/` · `tourist-no-show/` | gid | Javob, bekor qilish, "turist kelmadi" |
| GET / POST / DELETE | `/api/v1/cabinet/guide/unavailable-dates/` | gid | Ishlamaydigan kunlar |

**Jarayon:** so'rov (`requested`) → gid **24 soat** ichida qabul qiladi (`accepted`) yoki rad etadi; javob bo'lmasa
`expired` → to'lov (hozircha admin: *"To'langan deb belgilash"*) → `confirmed` → xizmatdan keyin `completed`.
Gid va turist telefonlari bir-biriga faqat to'lovdan keyin ko'rinadi.

**Narx:** yarim kun (4 soat) / to'liq kun (8 soat) / ko'p kunlik (kun × narx, 2–14 kun). Guruh **5+** kishi —
**+20%** (gid o'zgartiradi). LAZURI — **15%**, gid — **85%**.

**Bekor qilish va jarimalar** (taqdimot, `apps/guides/policies.py`):

| Kim | Qolgan vaqt | Turistga | Gidga |
|---|---|---|---|
| Turist | ≥ 48 s / 24–48 s / 12–24 s / < 12 s | 100% / 50% / 25% / 0% | — |
| Gid | ≥ 72 s / 48–72 s / 24–48 s / < 24 s | 100% | — / $5 / $10 + 1 ogohl. / $20 + 2 ogohl. |
| Turist kelmadi | gid 1 soat kutgach belgilaydi | 0% | jami summaning 30% |
| Gid kelmadi | admin belgilaydi | 100% | $25; **3 marta — profil bloklanadi** |

Reyting 5+ sharhdan keyin **4.0 dan past** tushsa — profil vaqtincha to'xtatiladi.

### Mehmonxonalar

| Metod | Endpoint | Kim | Vazifa |
|---|---|---|---|
| GET | `/api/v1/hotels/` | hamma | `?destination=&stars=4&kind=hotel&amenity=wifi&max_price=` + `check_in&check_out&guests&rooms` (faqat bo'sh xonalilar) |
| GET | `/api/v1/hotels/{slug}/` | hamma | Mehmonxona, rasmlar, kirish/chiqish vaqti, bekor qilish shartlari |
| GET | `/api/v1/hotels/{slug}/rooms/` | hamma | Xona turlari; sanalar bilan — `available_rooms`, `nights`, `stay_total_uzs` |
| GET | `/api/v1/hotels/{slug}/reviews/` | hamma | Sharhlar |
| GET / POST / PATCH | `/api/v1/hotels/me/` | login | Mehmonxonani ro'yxatdan o'tkazish arizasi / profil |
| POST | `/api/v1/hotel-bookings/` | login | Bron: `room_type`, `check_in`, `check_out`, `rooms`, `guests`, kontakt → **30 daqiqa** band |
| GET | `/api/v1/hotel-bookings/` · `{code}/` | login | O'z bronlari (raqam `LH...`) |
| GET / POST | `/api/v1/hotel-bookings/{code}/cancel-preview/` · `cancel/` · `review/` | login | Bekor qilish, sharh |
| CRUD | `/api/v1/cabinet/hotel/rooms/` · `images/` | mehmonxona | Xona turlari, rasmlar |
| GET / POST | `/api/v1/cabinet/hotel/bookings/` · `{code}/cancel/` | mehmonxona | Bronlar; bekor qilsa mehmonga 100% |
| GET / POST | `/api/v1/cabinet/hotel/reviews/` · `{id}/reply/` | mehmonxona | Sharhlar va javob |

- Bo'sh xonalar **har kecha bo'yicha** hisoblanadi (jami − faol bronlar); muddati o'tgan to'lanmagan bron joy egallamaydi.
- Narx = kecha narxi × kechalar × xonalar (≤ 30 kecha). Komissiya sukut 15%.
- Bekor qilish siyosati turlardagidek (`free` / `partial` / `non_refundable`), kirish vaqtiga nisbatan.

### Umumiy qoidalar

- **Sahifalash:** har sahifada 20 ta, `?page=2`, `?page_size=50` (maks. 100).
  Javob: `{"count", "next", "previous", "results"}`.
- **So'rovlar chegarasi:** anonim — 100/daq, foydalanuvchi — 300/daq, `register`/`login` — 10/daq.
- **Ko'rinish:** `is_published=False` bo'lgan shahar va joylarni faqat admin ko'radi.
  Shahar yashirilsa, uning joylari ham yashirinadi.
- **Xatolar:** `400` — validatsiya (maydon → xabarlar ro'yxati), `401` — token yo'q yoki yaroqsiz,
  `403` — ruxsat yo'q, `404` — topilmadi, `429` — juda ko'p so'rov.

## Telegram bildirishnomalari (faqat adminlar)

Adminlarga quyidagi hodisalarda xabar keladi (admin panel havolasi bilan):

| Hodisa | Xabar |
|---|---|
| Yangi bron | 🆕 bron raqami, tur, sana, kishilar, summa, agentlik, turist kontakti |
| Bron bekor qilindi | ❌ kim bekor qildi, qaytariladigan summa, sabab |
| Agentlik sanani bekor qildi | 🚫 bitta umumiy xabar: nechta bron, jami qaytarish |
| Agentlik arizasi | 🏢 nomi, mas'ul shaxs, telefon |
| Tur moderatsiyaga yuborildi | 🧭 tur, agentlik, narx |
| Yangi sharh | 💬 baho (3 va past — ⚠️), matn |

**Sozlash:**

1. Telegram'da **@BotFather** → `/newbot` → tokenni oling va `.env` ga yozing: `TELEGRAM_BOT_TOKEN=...`
2. `docker compose restart web scheduler`
3. Har bir admin botga `/start` yozadi (yoki botni admin guruhiga qo'shing).
4. `docker compose exec web python manage.py telegram_chat_ids` → chiqqan ID'larni `.env` ga:
   `TELEGRAM_ADMIN_CHAT_IDS=123456789,987654321`
5. `docker compose restart web scheduler` va sinov: `docker compose exec web python manage.py telegram_test`

Xabarlar avval bazaga yoziladi (admin panel → *Telegram xabarlari*), `scheduler` 15 soniyada yuboradi;
xato bo'lsa 5 martagacha qayta urinadi. Telegram sekinlashsa ham sayt kutib qolmaydi.
Token sozlanmagan bo'lsa — hech narsa yozilmaydi. Testlar hech qachon haqiqiy Telegram'ga yozmaydi.

## Telegram bot orqali ro'yxatdan o'tish

Saytda **"Telegram orqali kirish"** tugmasi → `t.me/<bot>?start=login` → bot:

1. telefon raqamini so'raydi (**📱 Telefon raqamni yuborish** tugmasi — faqat o'zining kontakti qabul qilinadi,
   raqamni qo'lda yozib bo'lmaydi; hozircha faqat +998);
2. yangi foydalanuvchidan ism-familiyani so'raydi (Telegram'dagi ism tugma sifatida taklif qilinadi);
3. foydalanuvchini bazaga yozadi — shu raqamli akkaunt bo'lsa, Telegram unga ulanadi (yangi akkaunt ochilmaydi);
4. bir martalik havola yuboradi: `<LAZURI_FRONTEND_URL>/auth/telegram?code=...` (10 daqiqa, bir marta ishlaydi).
   Havola bosilganda sayt `POST /api/v1/auth/telegram/login/ {"code": "..."}` orqali kiradi.

Qaytgan foydalanuvchi `/start` bosishi bilan darhol yangi havola oladi. `/id` — chat ID'ni ko'rsatadi.

**Sozlash:** bildirishnomalar boti bilan bitta bot ishlatiladi.

1. `.env`: `TELEGRAM_BOT_TOKEN=...`, `TELEGRAM_BOT_USERNAME=<bot username, @ siz>`
2. Botni ishga tushiring (dev, long polling): `python manage.py telegram_bot` — alohida terminalda ishlab turadi.
3. Prod: `TELEGRAM_WEBHOOK_SECRET` va `LAZURI_FRONTEND_URL` ni yozing, so'ng bir marta
   `python manage.py telegram_bot --set-webhook https://<domen>/api/v1/auth/telegram/webhook/`.
   Dev'ga qaytish: `python manage.py telegram_bot --delete-webhook`.

Dev'da (`localhost`) Telegram havolani tugma qilib ko'rsata olmaydi — bot uni matn sifatida yuboradi.
Bot ishlab turganda `telegram_chat_ids` buyrug'i bo'sh chiqishi mumkin (xabarlarni bot o'qib oladi) — o'rniga botga `/id` yozing.

## Foydalanuvchilarga bildirishnomalar (email / SMS)

Muhim xabarlar — email **va** SMS (telefon tasdiqlangan bo'lsa yoki tashkilot telefoni), qolganlari — email.
Xabarlar navbatga yoziladi (admin panel → *Email / SMS xabarlari*), `scheduler` yuboradi, 5 martagacha qayta urinadi.
Tasdiqlash kodlari navbatsiz, darhol yuboriladi.

| Kimga | Qachon |
|---|---|
| Turist | bron yaratildi; tasdiqlandi (SMS); tashkilotchi bekor qildi (SMS); gid qabul qildi / rad etdi / javob bermadi |
| Agentlik (email + xodimlar) | yangi to'langan bron (SMS); turist to'langan bronni bekor qildi; tur tasdiqlandi / rad etildi; ariza natijasi |
| Gid | **yangi so'rov (SMS — 24 soatda javob kerak)**; bron to'landi (SMS); turist bekor qildi; profil holati |
| Mehmonxona | yangi to'langan bron (SMS); mehmon bekor qildi; mehmonxona holati |

> SMS hozircha `console` rejimida — matn server logiga chiqadi (`docker compose logs web | grep SMS`).
> Haqiqiy SMS uchun provayder bilan shartnoma tuzilgach `apps/notifications/sms.py` ga backend qo'shiladi.

## Fayllar va maxfiylik

- **Yopiq fayllar:** gid sertifikatlari `private_media/` da (MEDIA'dan tashqarida), API ularni hech kimga qaytarmaydi
  (`has_certificate_file`). Admin panelda — *"yuklab olish"* havolasi (`/admin/private/...`, faqat `is_staff`).
- **Yuklash cheklovlari:** rasmlar — jpg/png/webp, ≤ 10 MB; video — mp4/mov/webm, ≤ 100 MB (muqova faqat rasm);
  hujjatlar — pdf/jpg/png, ≤ 10 MB; audio-gid — mp3/m4a/ogg, ≤ 30 MB.

## Production'ga chiqarish

```bash
cp .env.prod.example .env.prod      # qiymatlarni to'ldiring (SECRET_KEY, domen, Postgres paroli, SMTP...)
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

| Servis | Vazifa |
|---|---|
| `db` | PostgreSQL 16 (port tashqariga ochilmaydi) |
| `web` | gunicorn + `config.settings.prod`; ishga tushganda `migrate` va `collectstatic`; healthcheck `/api/health/` |
| `scheduler` | bronlar muddati, bildirishnomalar (15 s) |
| `frontend` | Next.js (standalone, prod) |
| `nginx` | 80-port: `/api/v1`, `/admin`, `/static` → backend; `/media/` — fayllar; qolgani → frontend. Yuklash ≤ 110 MB |
| `backup` | har kuni `pg_dump` → `./backups/lazuri-YYYYMMDD-HHMM.dump`, 14 kun saqlanadi |

- HTTPS'ni oldidagi proksi / load balancer yoki certbot beradi (`X-Forwarded-Proto` uzatilishi kerak).
- Static fayllar — whitenoise (alohida server kerak emas). Konteynerlar root bo'lmagan foydalanuvchi (uid 1000) bilan.
- Zaxiradan tiklash: `pg_restore -h db -U lazuri -d lazuri --clean backups/lazuri-....dump`
- **CI:** `.github/workflows/ci.yml` — har push'da ruff, migratsiya tekshiruvi, Postgres bilan pytest, `check --deploy`.

## Rollar va ruxsatlar

| Rol | Kim | Imkoniyatlar |
|---|---|---|
| `tourist` | Sayohatchi | Katalog, profil, agentlik arizasi |
| `agency` | Turagentlik xodimi | + agentlik kabineti (ariza tasdiqlanganda avtomatik beriladi) |
| `guide` | Individual gid | Turist bilan bir xil (gid profili — keyingi bosqichlarda) |
| `business` | Mehmonxona, restoran va h.k. | Turist bilan bir xil (keyingi bosqichlarda) |
| `admin` | LAZURI jamoasi | Admin panel: arizalar, moderatsiya, komissiya, katalog |

`admin` rolini API orqali olib bo'lmaydi — faqat `createsuperuser` yoki admin panel orqali.
Katalogga yozish va moderatsiya huquqi `is_staff=True` ga bog'liq. Kabinetga kirish — `AgencyMember` orqali
(bitta foydalanuvchi — bitta agentlik; agentlik `suspended` bo'lsa kabinet yopiladi).

## Biznes qoidalari

Joriy model — triphub.uz. Batafsil: `.claude/skills/lazuri-business-rules/SKILL.md`.

**Amalda (kodda bor):**

- **Gidlar va mehmonxonalar:** yuqoridagi bo'limlarga qarang.
- **LAZURI ham agentlik:** `is_platform=True`, komissiya 0%, `auto_publish=True` — o'z turlarini moderatsiyasiz chiqaradi.
- **Agentlik onboarding'i:** ariza → admin tekshiruvi (maqsad: 24 soat) → agentlik yaratiladi, "tekshirilgan" belgisi.
- **Komissiya:** har bir agentlik uchun alohida `commission_percent`, sukut bo'yicha 15%.
- **Narx:** 1 kishi uchun, so'mda. Sana uchun maxsus narx qo'yish mumkin (`Departure.price_uzs`).
- **Muddatli to'lov:** 12 oy, jami = narx × 1.44, oylik = jami ÷ 12 (890 000 → 106 800/oy).
- **Bekor qilish siyosatlari** (`apps/tours/policies.py`):
  - `free` — jo'nashdan ≥ 24 soat oldin 100% qaytariladi, keyin 0%;
  - `partial` — jo'nashdan > 48 soat oldin 50%, keyin 0%;
  - `non_refundable` — 0%.
  Turist bekor qilsa — siyosat bo'yicha; **agentlik yoki admin bekor qilsa — doim 100%**. Jo'nash vaqti =
  sana + turning `departure_time` (Toshkent vaqti). Jo'nagandan keyin turist bekor qila olmaydi.
- **Bron** (`apps/bookings/services.py`): sana va joylar soni tanlanadi → joylar **30 daqiqaga** band qilinadi
  (Postgres qulfi bilan — bir vaqtda kelgan so'rovlar ortiqcha sotolmaydi) → to'lanmasa `expired`, joylar qaytadi.
  Agentlik tasdig'i kerak emas. Narx, komissiya va siyosat bron paytida qotiriladi.
  Bitta foydalanuvchida bir vaqtda ko'pi bilan 3 ta to'lanmagan bron.

- **To'lov:** usullar ro'yxati — Payme, Click, Uzum Nasiya ("Tez kunda"). Shartnomalardan keyin: rasmiy merchant
  API (avtomatik tasdiq), Uzum Nasiya muddatli to'lov, agentlikka pul o'tkazish va qaytarishlar hisobi.

## Yo'l xaritasi

- [x] **1-bosqich:** loyiha skeleti, foydalanuvchilar + JWT, katalog (yo'nalish, joy)
- [x] **2-bosqich:** turagentliklar — ariza, tekshiruv, agentlik profili, kabinet
- [x] **3-bosqich:** turlar — toifalar, dastur, media, jo'nash sanalari, filtrlar, moderatsiya, muddatli to'lov hisobi
- [x] **4-bosqich:** bronlar — 30 daqiqalik band qilish, sayohatchilar, bekor qilish va qaytariladigan summa, agentlik bronlari
- [ ] **5-bosqich:** to'lovlar — Payme, Click, Uzum Nasiya (hozir ro'yxatda "Tez kunda"; kod shartnomalardan keyin),
  agentlikka pul o'tkazish va qaytarishlar
- [x] **6-bosqich:** sharhlar va reyting, agentlik javobi, blog ("Qo'llanmalar"), FAQ, sahifalar,
  adminlarga Telegram bildirishnomalari
- [x] **8-bosqich:** parolni tiklash, email tasdiqlash, telefon + SMS bilan kirish; foydalanuvchilarga email/SMS;
  yopiq fayllar va yuklash cheklovlari; production (gunicorn, nginx, zaxira, Sentry, CI)
- [x] **7-bosqich:** individual gidlar va mehmonxonalar (to'liq). AI marshrut va ko'p tilli kontent (uz, ru, en) —
  "Tez kunda" (`/api/v1/features/`)

## Muammolar va yechimlar

| Muammo | Yechim |
|---|---|
| WSL'da `docker: command not found` | Docker Desktop → Settings → Resources → WSL Integration → distributivni yoqing |
| `connection refused ... 5432` | Postgres ishlamayapti: `docker compose up -d db` |
| `Set the DJANGO_SECRET_KEY environment variable` | `prod` sozlamalari kalitsiz ishlamaydi — `.env` ga yozing |
| Port 5432 yoki 8000 band | `docker-compose.yml` dagi `ports` ni o'zgartiring (masalan `"5433:5432"`) va `DATABASE_URL` ni moslang |
| `relation ... does not exist` | `python manage.py migrate` |
| SMS kod kelmayapti (dev) | Kod server logida: `docker compose logs web \| grep SMS` |
| Email kelmayapti (dev) | `EMAIL_URL=consolemail://` — xat `docker compose logs scheduler` / `web` da |
