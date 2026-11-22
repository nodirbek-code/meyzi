---
name: meyzi-business-rules
description: MEYZI biznes qoidalari — TripHub (triphub.uz) modeli bo'yicha agentlik → tur → jo'nash sanasi → bron → to'lov; komissiya, muddatli to'lov, bekor qilish siyosatlari, 30 daqiqalik band qilish, moderatsiya, MEYZI'ning o'z turlari. Agentliklar, turlar, bronlar, to'lovlar, sharhlar kodini yozishda albatta ishlating.
---

# MEYZI: biznes qoidalari

**Asosiy model — [triphub.uz](https://www.triphub.uz/)** (foydalanuvchi qarori, 2026-11-20): "TripHub qanday ishlasa,
shunday qilamiz". Ustiga MEYZI'ning o'z qo'shimchalari: platforma faqat agregator emas — **o'zi ham tur yaratadi**
va yangi xizmatlar qo'shadi.

Raqamlarni kodga qattiq yozmang: sozlama (`config/settings/base.py` → `MEYZI_*`), model maydoni yoki
`apps/<app>/policies.py` konstantasi qiling va test bilan mahkamlang. Noaniq joyda foydalanuvchidan so'rang.

## Ishtirokchilar

| Kim | Model | Izoh |
|---|---|---|
| Turist | `User(role=tourist)` | Qidiradi, bron qiladi, to'laydi, sharh yozadi |
| Turagentlik | `Agency` + `AgencyMember(user, role=owner/manager)` | Turlarni o'tkazadi. Bitta user — bitta agentlik |
| MEYZI | `Agency(is_platform=True, auto_publish=True, commission_percent=0)` | Platformaning o'z turlari (`seed_tours` yaratadi) |
| Admin | `User(is_staff=True)` | Arizalar, moderatsiya, komissiya |

## Agentlik onboarding'i (amalda)

1. Ariza: `agency_name`, `contact_person`, `phone` (+ email, izoh). Login shart emas, lekin login bilan yuborilsa —
   tasdiqlangach shu user agentlik egasi (`owner`) bo'ladi va roli `agency` ga o'tadi.
2. Admin tekshiradi (maqsad — 24 soat ichida), hujjatlar: STIR, litsenziya.
3. `approve` → `Agency(is_verified=True)` yaratiladi (slug takrorlansa `-2`, `-3`). `reject` → izoh bilan.
4. Agentlik `suspended` bo'lsa: turlari katalogdan yo'qoladi, kabinet yopiladi.

## Turlar (amalda)

- Tur maydonlari (TripHub tur sahifasi bo'yicha): nomi, yo'nalish, toifalar, kun/kecha, maks. guruh,
  jo'nash/qaytish vaqti, uchrashuv joyi (+ koordinata, xarita havolasi), narx (1 kishi, so'm) + narx izohi,
  kiradi / kirmaydi / o'zingiz bilan oling (ro'yxatlar), kunlik dastur (vaqt oraliqlari, "o'z hisobidan" belgisi),
  media (rasm/video, bitta muqova), bekor qilish siyosati.
- Toifalar — model (`TourCategory`), admin qo'shadi: Tog', Madaniy, Sarguzasht, Dam olish kuni...
- **Holatlar:** `draft` → `submit` → `pending_review` → admin → `published`; `rejected` (+ `moderation_note`),
  `archived`. `auto_publish` agentlikda `submit` → darhol `published`. Yuborish uchun kamida 1 rasm.
- **Ommaviy ko'rinish:** `status=published` + agentlik `active` + yo'nalish `is_published`.
- **Jo'nash sanasi** (`Departure`): sana, jami joy, band joy, ixtiyoriy maxsus narx, holat (open/closed/cancelled).
  Bir turda bir sana bir marta. O'tgan sana qo'shilmaydi. Band joydan kam qilib bo'lmaydi. Bronli sana o'chirilmaydi.
  Bronli tur o'chirilmaydi — arxivlanadi.

## Narx va muddatli to'lov (amalda — `apps/tours/pricing.py`)

- Narx so'mda, butun son, 1 kishi uchun. Bolalar/guruh chegirmasi TripHub'da yo'q — kerak bo'lsa keyin qo'shiladi.
- Muddatli to'lov (Uzum Nasiya kabi): **jami = narx × 1.44**, **oylik = jami ÷ 12**, so'mgacha `ROUND_HALF_UP`.
  Tekshiruv: 890 000 → 106 800/oy; 170 000 → 20 400/oy.

## Bekor qilish siyosatlari (amalda — `apps/tours/policies.py`)

Har bir tur uchtasidan birini tanlaydi; turist to'lashdan **oldin** ko'radi.

| Siyosat | Qoida |
|---|---|
| `free` | Jo'nashdan **≥ 24 soat** oldin — 100%; undan kam — 0% |
| `partial` | Jo'nashdan **> 48 soat** oldin — 50%; 48 soat va kam — 0% |
| `non_refundable` | 0% |

Chegaralar: `free` da aniq 24 soat → 100%; `partial` da aniq 48 soat → 0%.
Jo'nash vaqti = `Departure.date` + `Tour.departure_time` (Asia/Tashkent); vaqt bo'lmasa — kun boshi (00:00).

## Bron (amalda — `apps/bookings/services.py`)

1. Turist sana (`departure` id) va joylar sonini tanlaydi; kontakt (ism, telefon) majburiy; sayohatchilar ro'yxati
   ixtiyoriy (MEYZI qo'shimchasi), berilsa soni = joylar soni.
2. `create_booking` sanani `select_for_update` bilan qulflaydi, avval shu sanadagi eskirgan bronlarni bo'shatadi,
   so'ng joy yetarliligini tekshiradi va `seats_booked` ni oshiradi. Holat `pending_payment`,
   `expires_at = now + MEYZI_BOOKING_HOLD_MINUTES (30)`. Bir userda ≤ `MEYZI_MAX_PENDING_BOOKINGS (3)` to'lanmagan bron.
3. Muddat o'tsa — `expired`, joylar qaytadi: `scheduler` konteyneri har 60 s `process_bookings`, qo'shimcha ravishda
   ro'yxat/batafsil so'rovlarida va yangi bronda "lazy" tekshiruv.
4. To'lov o'tdi → `confirm_booking` → `confirmed` (idempotent). **Agentlik tasdig'i yo'q.** Muddati o'tgan bronni
   tasdiqlab bo'lmaydi (to'lov kechiksa — 5-bosqichda pulni qaytarish).
5. Qotiriladi: `unit_price_uzs` (sana maxsus narxi yoki tur narxi), `total_uzs`, `commission_percent`,
   `commission_uzs`, `agency_amount_uzs`, `cancellation_policy`, `departure_at` (sana + `departure_time`, Toshkent).
6. Bekor qilish: turist — siyosat bo'yicha (`refund_ratio`), jo'nagandan keyin mumkin emas; agentlik/admin —
   doim 100%; to'lanmagan bron — qaytarish 0. Agentlik sanani `cancelled` qilsa — barcha faol bronlar 100% bilan bekor.
   Bronli sana/tur o'chirilmaydi (bron `PROTECT`).
7. Sayohat tugagach (`departure_at + duration_days`) — `completed` (sharh yozish huquqi uchun).
8. `seats_booked` ni faqat bookings servislari o'zgartiradi — boshqa joyda qo'lda o'zgartirmang.

## To'lov (5-bosqich — kutilmoqda)

Foydalanuvchi qarori (2026-11-20): merchant shartnomalari yo'q; **to'lov kodi yozilmasin**, chek yuklash tizimi
ham kerak emas (yozilgan edi — olib tashlandi). Hozir faqat `GET /api/v1/payments/methods/`: Payme, Click,
Uzum Nasiya — `enabled: false`, `status_text: "Tez kunda"`, logotip `apps/payments/static/payments/<code>.svg|png`.

Shartnomalar tuzilib, foydalanuvchi so'raganda: provayderning rasmiy hujjati bo'yicha (taxmin qilmasdan) webhook,
imzo tekshiruvi, idempotentlik, summa solishtirish; muvaffaqiyatda `bookings.services.confirm_booking`.
Agentlikka `agency_amount_uzs` o'tkaziladi. Hozircha bron admin panel → *"To'langan deb belgilash"* bilan tasdiqlanadi.

## Sharhlar (amalda — `apps/reviews/`)

Faqat `completed` bron egasi, bitta bronga bitta, baho 1–5, 14 kun ichida tahrirlash. `recalculate_ratings`
tur va agentlik `rating`/`reviews_count` ni faqat `published` sharhlardan hisoblaydi (2 xona, ROUND_HALF_UP).
Admin yashiradi (`hidden`). Agentlik javob beradi. Ommaga muallif "Ism F." (email/familiya to'liq emas).

## Kontent (amalda — `apps/content/`)

Article (Qo'llanmalar, TripHub /guides kabi), FaqItem (`seed_content`), Page (`terms`, `privacy` — matnni
foydalanuvchi yozadi, o'zingiz yuridik matn to'qimang).

## Telegram bildirishnomalari (amalda — `apps/notifications/`)

**Faqat adminlar uchun** (foydalanuvchi qarori). Turist/agentlikka Telegram yuborilmaydi.
Servislardan `notify.<hodisa>(...)` chaqiriladi → `TelegramMessage` (outbox) → `scheduler` 15 s da yuboradi,
5 marta qayta urinadi. Sozlanmagan bo'lsa yozilmaydi. Foydalanuvchi matni doim `html.escape`.
Yangi hodisa qo'shsangiz — `services.py` ga funksiya va test (`tests/test_notifications.py` dagi `tg` fixture).
Test sozlamalari tokenni majburan bo'shatadi.

## Autentifikatsiya va bildirishnomalar (amalda)

- Kirish: email + parol yoki telefon + SMS kod (`+998XXXXXXXXX`, akkaunt avtomatik yaratiladi, parolsiz).
  `User.email` ham `phone` ham ixtiyoriy (kamida bittasi), ikkalasi unique. Email/telefon faqat kod orqali o'zgaradi.
- Kodlar (`apps/accounts/otp.py`): 6 raqam, HMAC-xesh, 10 daq, 5 urinish, 60 s qayta yuborish, soatiga 5.
  Kod tekshiruvchi view'lar `transaction.non_atomic_requests` (urinishlar orqaga qaytmasin) — yangi kod view'i ham shunday bo'lsin.
- Foydalanuvchi xabarlari: `apps/notifications/user_events.py` → `UserMessage` outbox (email/SMS) → scheduler.
  Shoshilinch — SMS ham (gidga yangi so'rov, tasdiqlash, provayder bekor qilishi). SMS faqat `phone_verified` foydalanuvchiga
  yoki tashkilot telefoniga. SMS provayderi yo'q (`SMS_BACKEND=console`) — protokolni taxmin qilib yozmang.
- Yopiq fayllar: `apps.core.files.private_storage` (sertifikatlar), URL — `/admin/private/...` faqat staff.
  Yangi fayl maydoniga doim `image_rule`/`video_rule`/`document_rule` validatori.

## Tillar va "Tez kunda" imkoniyatlar (foydalanuvchi qarori, 2026-11-20)

- Tillar boshlanishiga **faqat 3 ta: uz, ru, en** (`settings.LANGUAGES`, `User.Language`). Boshqa til qo'shmang.
- Ko'p tilli kontent (tarjima) **hozircha qo'shilmaydi** — `features.multilingual_content.enabled = false`.
  Qo'shilganda aynan shu 3 til bilan (masalan, django-modeltranslation yoki `*_ru`, `*_en` maydonlar).
- **AI marshrut** — "Tez kunda", kod yozilmaydi (`apps/core/features.py`).
- Yangi "Tez kunda" imkoniyat — `features()` ga `{"enabled": False, "status_text": "Tez kunda"}` bilan qo'shiladi.

## Individual gidlar (amalda — `apps/guides/`, qoidalar `policies.py`)

Foydalanuvchi qarori (2026-11-20): gidlar va mehmonxonalar **to'liq** ishlaydi, faqat AI marshrut "Tez kunda".
- Profil: `/guides/me/` ariza → `pending` → admin `approve` (taqdimot: 48 soat). Rad etilgan profil tahrirlansa — qayta `pending`.
- Narx: yarim/to'liq/ko'p kunlik (2–14 kun), guruh ≥ `MEYZI_GUIDE_GROUP_THRESHOLD` (5) → +`group_surcharge_percent` (20%).
  Komissiya 15% (gid 85%). Narx so'rov paytida qotiriladi.
- Oqim: `requested` (gid 24 soatda javob, aks holda `expired`) → `accepted` → to'lov (`mark_paid`, hozir admin) → `confirmed` →
  `completed`. Gid kunlari: `GuideUnavailableDate` + faol bronlar (ko'p kunlik — barcha kunlar). Gid qulfi `select_for_update`.
- Bekor qilish: turist 48/24/12 soat → 100/50/25/0% (faqat to'langan bo'lsa); gid → turistga 100%, jarima $5/$10(+1)/$20(+2)
  (72/48/24 soat chegaralari); gid `requested` ni bekor qilmaydi — `decline`. Turist kelmadi (1 soat kutish) → 0%, gidga 30%.
  Gid kelmadi (admin) → 100%, $25, 3 marta → `suspended`. Reyting < 4.0 (≥ 5 sharh) → `suspended`.
- Kontaktlar (telefonlar) to'lovdan keyingina ochiladi.

## Mehmonxonalar (amalda — `apps/hotels/`)

- Ariza `/hotels/me/` → `pending` → admin. Egasi `HotelMember` (bitta user — bitta mehmonxona), roli `business`.
- `RoomType`: sig'im, kecha narxi, `total_rooms`. Bo'sh xonalar — har kecha uchun `total − faol bronlar`
  (`confirmed` + muddati o'tmagan `pending_payment`), `select_for_update` xona turi ustida.
- Bron: ≤ 30 kecha, mehmonlar ≤ sig'im × xonalar, 30 daqiqa band, admin `mark_paid`. Kirish vaqti = check_in + `check_in_time`.
- Bekor qilish: `apps/tours/policies.refund_ratio` (free/partial/non_refundable) kirish vaqtiga nisbatan; mehmonxona/admin → 100%.
- `check_out` kuni o'tgach `completed` → sharh.

## MEYZI qo'shimchalari (7-bosqich, `D:\proyekt\MEYZI.pptx` dan)

TripHub'da yo'q, MEYZI o'zi qo'shadi (gidlar va mehmonxonalar — amalda, yuqorida),
diqqatga sazovor joylar katalogi (`catalog.Place`, audio-gid), ko'p tillilik,
AI marshrut, oflayn rejim, mobil ilova. Taqdimotdagi gid jarimalari va 48/24/12 soat qoidasi faqat
**individual gidlar** moduliga tegishli — turlarga emas.
