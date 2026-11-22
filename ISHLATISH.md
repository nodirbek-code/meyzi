# MEYZI — ishlatish yo'riqnomasi

MEYZI — O'zbekiston bo'ylab turlar, gidlar va mehmonxonalarni onlayn bron qilish platformasi.
Bu yo'riqnomada platformani **ishga tushirish**, **sozlash** va **har bir foydalanuvchi turi uchun ishlatish** tushuntirilgan.
Texnik tafsilotlar (API, kod tuzilmasi) — `README.md` da.

---

## Mundarija

1. [Ishga tushirish](#1-ishga-tushirish)
2. [Sozlash (.env)](#2-sozlash-env)
3. [Sayohatchi (turist) uchun](#3-sayohatchi-turist-uchun)
4. [Turagentlik uchun](#4-turagentlik-uchun)
5. [Gid uchun](#5-gid-uchun)
6. [Mehmonxona uchun](#6-mehmonxona-uchun)
7. [Administrator uchun](#7-administrator-uchun)
8. [Nom, logo va ranglarni o'zgartirish](#8-nom-logo-va-ranglarni-ozgartirish)
9. [Tekshirish va testlar](#9-tekshirish-va-testlar)
10. [Serverga chiqarish (production)](#10-serverga-chiqarish-production)
11. [Ko'p uchraydigan muammolar](#11-kop-uchraydigan-muammolar)

---

## 1. Ishga tushirish

**Kerak:** Docker Desktop (yoqilgan), Git.

```bash
cd D:\meyzi                  # WSL'da: cd /mnt/d/meyzi
copy .env.example .env        # WSL/Linux'da: cp .env.example .env
docker compose up -d --build
```

Birinchi ishga tushirishda bir necha daqiqa kuting (frontend `npm install` qiladi). Ko'tariladigan qismlar:

| Qism | Manzil | Vazifasi |
|---|---|---|
| **Sayt** (frontend) | http://localhost:3000 | Foydalanuvchilar ko'radigan sayt |
| **API** (backend) | http://localhost:8000/api/docs/ | Barcha endpoint'lar (Swagger) |
| **Admin panel** | http://localhost:8000/admin/ | Arizalar, moderatsiya, to'lovni tasdiqlash |
| Baza | localhost:5432 | PostgreSQL |
| Scheduler | — | Muddati o'tgan bronlarni bekor qiladi, xabarlarni yuboradi |

**Administrator yaratish va demo ma'lumot yuklash** (bir marta):

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo    # turlar, toifalar, shaharlar, FAQ, 2 gid, 2 mehmonxona
```

**To'xtatish:** `docker compose down` (ma'lumotlar saqlanadi). Bazani butunlay tozalash: `docker compose down -v`.

**Holatni ko'rish:** `docker compose ps`, loglar: `docker compose logs web --tail 50` (yoki `frontend`, `scheduler`).

---

## 2. Sozlash (.env)

`.env` faylida (loyiha ildizida) asosiy sozlamalar. O'zgartirgandan keyin: `docker compose up -d` (qayta ishga tushadi).

### 2.1. Telefon tasdiqlash kodlari — Telegram

Sayt telefon raqamlarini **SMS emas, Telegram orqali** kod yuborib tasdiqlaydi (Telegram Gateway — kod to'g'ridan-to'g'ri
raqamga bog'langan Telegram akkauntiga keladi, botga kirish shart emas).

| O'zgaruvchi | Qiymat |
|---|---|
| `TELEGRAM_CODE_BACKEND` | `console` — kod faqat server logiga chiqadi (ishlab chiqish uchun) · `gateway` — haqiqiy yuborish |
| `TELEGRAM_GATEWAY_TOKEN` | https://gateway.telegram.org → hisob sozlamalari → **API token** |

> **Ishlab chiqishda kodni qayerdan olaman?** `TELEGRAM_CODE_BACKEND=console` bo'lsa, kod logda chiqadi:
> `docker compose logs web --tail 20` → `[TELEGRAM KOD] +998901234567: 123456`

Telegram Gateway pullik (har bir yetkazilgan xabar uchun). Yetkazilmagan xabar puli qaytariladi.

### 2.2. Google orqali kirish

| O'zgaruvchi | Qiymat |
|---|---|
| `GOOGLE_CLIENT_ID` | Google Cloud Console → APIs & Services → Credentials → **OAuth client ID** (turi: Web application) |

Client ID yaratishda **Authorized JavaScript origins** ga sayt manzilini qo'shing: `http://localhost:3000`
(ishlab chiqish) va `https://meyzi.uz` (production). Bo'sh qoldirilsa — "Google orqali kirish" tugmasi "tez kunda" bo'lib turadi.

### 2.3. Boshqalar

| O'zgaruvchi | Izoh |
|---|---|
| `BRAND_NAME` | Email/SMS matnlaridagi loyiha nomi (sukut: `MEYZI`) |
| `EMAIL_URL` | Email yuborish. Ishlab chiqishda `consolemail://` (logga). SMTP: `smtp+tls://login:parol@smtp.server.uz:587` |
| `DEFAULT_FROM_EMAIL` | Jo'natuvchi: `MEYZI <no-reply@meyzi.uz>` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_IDS` | Adminlarga Telegram bildirishnomalari (yangi ariza, yangi bron). Chat ID: `docker compose exec web python manage.py telegram_chat_ids` |
| `SMS_BACKEND` | Bildirishnoma SMS'lari (kirish emas). Provayder ulanmaguncha `console` |

---

## 3. Sayohatchi (turist) uchun

### 3.1. Ro'yxatdan o'tish va kirish — http://localhost:3000/login

Uch usul:

1. **Telefon (Telegram)** — tavsiya etiladi.
   `+998` qotirilgan, faqat qolgan 9 raqamni yozasiz (`90 123 45 67`) → **«Telegram'ga kod yuborish»** →
   Telegram'ga kelgan 6 xonali kodni kiriting. Akkaunt bo'lmasa — avtomatik yaratiladi.
   Kodni qayta so'rash — 60 soniyadan keyin.
2. **Google** — «Google orqali kirish» (`GOOGLE_CLIENT_ID` sozlangan bo'lsa).
3. **Email va parol** — «Ro'yxatdan o'tish» sahifasida; emailga tasdiqlash kodi keladi.
   Parolni unutsangiz — «Parolni unutdingizmi?».

### 3.2. Tur topish

- **Bosh sahifa** — qidiruv (qayerga / qachon / sayohat turi), **sana tasmasi** (nuqtali kunlarda tur bor), mashhur turlar.
- **Turlar katalogi** (`/tours`) — chapda filtrlar: qidiruv, joylashuv, kategoriya, narx, davomiylik (1 kun / 2–3 kun / 4+),
  «Faqat bepul bekor qilish». Yuqorida — sana tasmasi va saralash. Faol filtrlar yorliq bo'lib chiqadi, ✕ bilan olib tashlanadi.

### 3.3. Turni bron qilish

Tur sahifasida o'ng tomondagi (telefonda — pastdagi «Bron qilish») panel:

1. **Ketish sanasini** tanlang (kartochkada nechta joy qolgani ko'rsatiladi).
2. **O'rinlar sonini** belgilang (− / +).
3. **Sayohatchilar** — har bir o'rin uchun ism va familiya.
4. **Aloqa** — ism va **telefon**. Telefon Telegram kodi bilan tasdiqlanadi: raqamni yozing → «Kod olish» → kodni kiriting →
   «✓ Tasdiqlangan». Akkauntingizdagi tasdiqlangan raqamga kod so'ralmaydi.
5. **«Bron qilish»** — o'rinlar **30 daqiqaga** siz uchun band qilinadi.

**Uchrashuv joyi** tur sahifasida (havorang blok) — «Xaritada ochish» bilan.

### 3.4. Bronlarim — `/account`

- Barcha bronlar (turlar, gidlar, mehmonxonalar) holati bilan: «To'lov kutilmoqda», «Tasdiqlangan», «Bekor qilingan»…
- Bron sahifasida: **to'lov muddati taymeri**, to'lov usuli (to'liq yoki 12 oyga bo'lib), uchrashuv joyi, sayohatchilar.
- **Onlayn to'lov hozircha ishlamaydi** («tez kunda») — to'lovni administrator tasdiqlaydi (7.3-bo'lim).
- **Bekor qilish** — «Bekor qilish» tugmasi qancha pul qaytishini oldindan ko'rsatadi (tur siyosatiga qarab).
- Sayohat tugagach — **sharh** qoldirish mumkin.

### 3.5. Gid bron qilish — `/guides`

Gid sahifasida: davomiylik (yarim kun / to'liq kun / bir necha kun), sana, vaqt, shahar, til →
**uchrashuv joyi — faqat gid belgilagan ro'yxatdan tanlanadi** (o'zingiz manzil yoza olmaysiz) → telefon (Telegram kod) →
«So'rov yuborish». Gid **24 soat** ichida javob beradi; qabul qilgach — to'lov.

### 3.6. Mehmonxona — `/hotels`

Sanalarni tanlang → bo'sh xonalar va narx chiqadi → «Tanlash» → ism, telefon (Telegram kod) → «Bron qilish» (30 daqiqa band).

### 3.7. Profil — `/account/profile`

Ism, email tasdiqlash, **telefon ulash/almashtirish** (Telegram kod bilan). Ulangan raqamga bron formalarida qayta kod so'ralmaydi.

---

## 4. Turagentlik uchun

### 4.1. Hamkor bo'lish

1. **«Agentliklar uchun»** sahifasi (`/agencies`) → pastdagi forma: agentlik nomi, aloqa shaxsi, **telefon (Telegram kod)**, email, izoh.
   Kirib yuborsangiz, tasdiqlangach shu akkaunt agentlik egasi bo'ladi.
2. Administrator arizani tekshiradi (STIR, litsenziya) va tasdiqlaydi.
3. Tasdiqlangach — menyuda **«Boshqaruv paneli»** (`/cabinet`).

### 4.2. Kabinet — `/cabinet/agency`

Chap menyu: **Umumiy · Turlar · Bronlar · Sharhlar**.

- **Umumiy** — statistika va agentlik profili. Telefonni o'zgartirsangiz — Telegram kod so'raladi.
- **Turlar** → «Yangi tur»:
  - nom, yo'nalish, toifa, kun/kecha, narx (1 kishi), bekor qilish siyosati, jo'nash/qaytish vaqti;
  - **📍 Uchrashuv joyi (majburiy):** joy nomi/manzil **va** xaritadagi joyi — koordinatani (`41.311151, 69.279737`)
    yoki Yandex/Google xarita havolasini qo'ying, tizim koordinatani o'zi ajratadi («✓ Koordinata: …»);
  - narxga kiradi / kirmaydi / o'zingiz bilan oling (har biri yangi qatorda), kunlik dastur;
  - **rasm/video** yuklang (kamida bitta rasm shart);
  - **jo'nash sanalari** va joylar sonini qo'shing;
  - **«E'longa yuborish»** → moderatsiya → e'lon qilinadi.
- **Bronlar** — turistlar bronlari (kod, kontakt, sizga tegadigan summa), bekor qilish (turistga 100% qaytariladi).
- **Sharhlar** — sharhlarga javob yozish.

---

## 5. Gid uchun

1. **Kirish** → `/guides/become` («Gid bo'lish»): ism, **telefon (Telegram kod)**, o'zingiz haqingizda, shaharlar, tillar,
   yo'nalishlar, narxlar (yarim kun / to'liq kun / ko'p kunlik), tajriba, sertifikat (fayl faqat tekshiruvchilarga ko'rinadi).
2. Tekshiruv — 48 soat. Tasdiqlangach — `/cabinet/guide`.
3. **Albatta: «Uchrashuv joylarim»** — har bir shahar uchun kamida bitta joy qo'shing (nom, manzil, xaritadagi joyi —
   koordinata yoki havola). **Joy bo'lmagan shaharga turist bron qila olmaydi.** Bronlarda ishlatilgan joy o'chirilmaydi — nofaol bo'ladi.
4. **So'rovlar** — 24 soat ichida «Qabul qilish» yoki «Rad etish». Turist telefoni to'lovdan keyin ochiladi.
5. **Ishlamaydigan kunlarim** — band kunlarni belgilang.
6. Qoidalar: komissiya 15%; gid bekor qilsa — vaqtga qarab jarima; 3 marta kelmay qolish yoki reyting < 4.0 — profil to'xtatiladi.

---

## 6. Mehmonxona uchun

1. **Kirish** → `/hotels/join`: nomi, turi, shahar, yulduz, manzil, tavsif, **telefon (Telegram kod)**, email,
   qulayliklar, bekor qilish siyosati.
2. Tekshiruvdan so'ng — `/cabinet/hotel`: **Profil · Xonalar · Bronlar**.
3. **Xonalar** — xona turlari (sig'im, kecha narxi, xonalar soni). **Rasmlar** — birinchisi muqova.
4. **Bronlar** — mehmonlar bronlari, bekor qilish (mehmonga 100%).

---

## 7. Administrator uchun

Admin panel: http://localhost:8000/admin/ (1-bo'limda yaratilgan superuser bilan).

### 7.1. Arizalarni ko'rib chiqish

| Bo'lim | Amal (ro'yxatda belgilab, «Action» menyusidan) |
|---|---|
| **Agentlik arizalari** | «Tasdiqlash (agentlik yaratiladi)» / «Rad etish» |
| **Gidlar** | «✅ Tasdiqlash» / «❌ Rad etish» / «⛔ To'xtatish» (izohni profilda «moderator izohi» ga yozing) |
| **Mehmonxonalar** | «✅ Tasdiqlash» / «❌ Rad etish» / «⛔ To'xtatish» |

### 7.2. Turlar moderatsiyasi

**Turlar** → «Kutilmoqda» holatidagilar → «Tasdiqlash va e'lon qilish» yoki «Rad etish» (izohni tur sahifasida yozing —
agentlik ko'radi).

### 7.3. To'lovni tasdiqlash (onlayn to'lov ulanmaguncha)

Turist pul to'lagach (operator orqali):

- **Bronlar** → bronni belgilang → **«To'langan deb belgilash (tasdiqlash)»** → bron «Tasdiqlangan», turist va agentlikka xabar.
- **Gid bronlari** / **Mehmonxona bronlari** — xuddi shunday «To'langan deb belgilash».
- Bron **30 daqiqada** to'lanmasa — avtomatik bekor bo'ladi va joylar bo'shaydi.

### 7.4. Sharhlar va kontent

- **Sharhlar** — «Yashirish» / «E'lon qilish».
- **Maqolalar** (qo'llanmalar), **FAQ** (savol-javob), **Sahifalar**:
  **«Foydalanish shartlari» (`terms`) va «Maxfiylik siyosati» (`privacy`) matnlarini shu yerda yozing** —
  ular bo'lmasa footerdagi havolalar 404 beradi.
- **Shaharlar / joylar / toifalar** — katalog.

### 7.5. Telefon kodlari

Kodlar bazada faqat xesh ko'rinishida saqlanadi (admin panelda ko'rinmaydi). Cheklovlar: kod 10 daqiqa amal qiladi,
5 ta noto'g'ri urinish, qayta yuborish — 60 soniyadan keyin, bitta raqamga soatiga 5 ta.
Gid «kelmay qolgan» bo'lsa — **Gid bronlari** → «🚨 Gid kelmadi».

---

## 8. Nom, logo va ranglarni o'zgartirish

| Nima | Qayerda |
|---|---|
| Nom, shior, telefon, email, Telegram, Instagram | `frontend/src/lib/brand.ts` |
| Email/SMS matnlaridagi nom | `.env` → `BRAND_NAME` |
| Logo (header, footer) | `frontend/public/brand/meyzi-mark*.png`, `meyzi-wordmark*.png` (oq variantlari — to'q fon uchun) |
| Ilova ikonkasi | `frontend/public/brand/meyzi-app-icon-*.png` |
| Brauzer ikonkasi (favicon), iPhone ikonkasi | `frontend/src/app/icon.png`, `frontend/src/app/apple-icon.png` |
| Ilova maketi (bosh sahifa, «Tez kunda») | `frontend/public/brand/meyzi-app-mockup.jpg` |
| Logoning asl fayllari | `brand/` (loyiha ildizida) |
| Ranglar (palitra) | `frontend/tailwind.config.ts` — `forest` (asosiy), `sun` (urg'u), `clay`, `sky`, `sand`, `ink` |

> **Diqqat:** `brand.ts` dagi telefon, email va ijtimoiy tarmoq manzillari hozircha **namuna** — haqiqiylari bilan almashtiring.

---

## 9. Tekshirish va testlar

```bash
# backend testlari (≈240 ta)
docker compose exec web pytest
# kod sifati
docker compose exec web ruff check .
# frontend turlari
docker compose exec frontend npx tsc --noEmit
```

**Qo'lda tekshirish ro'yxati:**

- [ ] `/login` → telefon → kod logdan (`docker compose logs web --tail 20`) → kirildi.
- [ ] Tur sahifasi → sana, 2 o'rin, sayohatchilar, telefon → «Kod olish» → kod → «Bron qilish» → bron sahifasi, taymer ishlayapti.
- [ ] Tasdiqlanmagan telefon bilan bron **qilib bo'lmaydi**.
- [ ] Gid sahifasi → uchrashuv joyi faqat ro'yxatdan tanlanadi.
- [ ] Bron sahifasida va «Bronlarim»da bron kodi (LZ…) **ko'rinmaydi**.
- [ ] Admin → bron → «To'langan deb belgilash» → holat «Tasdiqlangan».
- [ ] Telefonda (brauzer kengligini kichraytiring) — menyu, pastki «Bron qilish» paneli.

---

## 10. Serverga chiqarish (production)

```bash
cp .env.prod.example .env.prod      # to'ldiring: DJANGO_SECRET_KEY, domen, Postgres paroli, SMTP,
                                    # TELEGRAM_CODE_BACKEND=gateway, TELEGRAM_GATEWAY_TOKEN, GOOGLE_CLIENT_ID
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py createsuperuser
```

Production'da **albatta**: `TELEGRAM_CODE_BACKEND=gateway` (aks holda foydalanuvchilarga kod bormaydi),
`DEBUG` o'chiq, HTTPS. Batafsil — `README.md` → «Production'ga chiqarish».

---

## 11. Ko'p uchraydigan muammolar

| Muammo | Yechim |
|---|---|
| «Telefon raqami tasdiqlanmagan» | Telefon maydonidagi «Kod olish» → Telegram kodi. Yoki profilda raqamni ulang. |
| Telegram'ga kod kelmayapti | `TELEGRAM_CODE_BACKEND=gateway` va to'g'ri token bormi? Raqamda Telegram ochilganmi? Ishlab chiqishda kod — logda. |
| «Kodni qayta so'rash uchun N soniya kuting» | 60 soniya kuting. Soatiga 5 tadan ko'p so'rab bo'lmaydi. |
| «Google orqali kirish — tez kunda» | `.env` ga `GOOGLE_CLIENT_ID` yozing, `docker compose up -d`. |
| Gid sahifasida «uchrashuv joyini belgilamagan» | Gid kabinetida «Uchrashuv joylarim» ga shu shahar uchun joy qo'shsin. |
| Turni e'longa yuborib bo'lmayapti | Kamida 1 rasm, uchrashuv joyi va xaritadagi joyi (koordinata yoki havola) shart. |
| Kod o'zgarishi saytda ko'rinmayapti | `docker compose restart web` (backend) yoki `docker compose restart frontend`. |
| `localhost:3000` ochilmayapti | `docker compose ps` — `frontend` ishlayaptimi? `docker compose logs frontend --tail 30`. |
| Footerdagi «Foydalanish shartlari» 404 | Admin → Sahifalar → `terms` va `privacy` sahifalarini yarating (7.4). |
