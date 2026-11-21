# LAZURI — xatolar va o'zgartirishlar ro'yxati

> **Holat (2026-11-21):** 1–5 bajarildi (backend + frontend). 6 — qismlab davom etmoqda.
> Yangi xato aytilganda shu faylga qo'shiladi. Bajarilganda holati `✅` ga o'zgaradi.

| # | Qisqacha | Holat |
|---|---|---|
| 1 | Telefon raqami tekshirilmaydi — `+998` qotirilgan, Telegram kod bilan tasdiqlash | ✅ (hamma formalar: bronlar, kirish, profil, agentlik/gid/mehmonxona arizalari, kabinet profillari) |
| 2 | Uchrashuv joyi majburiy va erkin yozilmasin (turlar, gidlar) | ✅ (tur: majburiy + xarita; gid: turist faqat gid belgilagan ro'yxatdan tanlaydi, gid kabinetida boshqaradi) |
| 3 | Bron oxirida chiqadigan kodni olib tashlash | ✅ (turist sahifalari va xabarlarida yo'q; hamkor kabineti va admin'da qoldi) |
| 4 | "SMS bilan kirish" o'rniga hamma joyda Telegram kod | ✅ |
| 5 | Google (Gmail) orqali kirish | ✅ (ishlashi uchun `GOOGLE_CLIENT_ID` kerak) |
| 6 | Frontend dizaynini `skrenshot/` papkadagi rasmlar asosida qayta yozish | 🔄 qismlab: bosh sahifa, katalog, tur sahifasi, kirish, bron sahifasi, gidlar, mehmonxonalar, hamkorlar sahifalari — ✅ |

---

## 1. Telefon raqami tekshirilmaydi

**Muammo:** telefon maydoniga istalgan narsa yozilsa ham qabul qilinyapti.

**Kerak:**
- Maydon boshida `+998` **qotirilgan** turadi, foydalanuvchi faqat qolgan 9 raqamni yozadi.
- Faqat raqam qabul qilinadi; uzunligi va formati tekshiriladi (masalan: `+998 90 123 45 67`).
- Raqam haqiqatan shu odamniki ekanini bilish uchun **shu raqamga Telegram orqali tasdiqlash kodi** yuboriladi.
- Telefon raqami **faqat kod to'g'ri kiritilgandan keyin** qabul qilinadi (saqlanadi).

**Qayerlarda (hozirgi kod bo'yicha):** ro'yxatdan o'tish / kirish, profil (telefon ulash), tur broni (aloqa telefoni),
gid so'rovi, mehmonxona broni, agentlik arizasi, gid arizasi, mehmonxona arizasi, kabinet profillari.

**Aniqlashtirish kerak:**
- Bron formasidagi "aloqa telefoni" ham har safar kod bilan tasdiqlanadimi yoki akkauntdagi tasdiqlangan raqam ishlatiladimi?
- Telegram'ga kod yuborish usuli: Telegram Gateway (rasmiy, raqamga to'g'ridan kod yuboradi, pullik) yoki LAZURI boti
  (foydalanuvchi avval botga kirib, kontaktini ulashishi kerak) — qaysi biri?

## 2. Uchrashuv joyi

**Muammo:** uchrashuv joyini kiritish majburiy emas va foydalanuvchilar uni xohlagan joyda belgilay olyapti.

**Kerak:**
- Ma'lumot kiritilayotganda uchrashuv joyi **majburiy** maydon bo'lsin.
- Foydalanuvchilar (turistlar) xohlagan joyda uchrasha olmasin — **turlar uchun ham, gidlar uchun ham**.

**Hozirgi holat (kod bo'yicha):**
- Tur: agentlik `meeting_point` ni kiritadi, lekin u majburiy emas.
- Gid broni: turist uchrashuv joyini **o'zi erkin matn** bilan yozadi.

**Aniqlashtirish kerak:** gid uchun uchrashuv joylarini kim belgilaydi — gid o'z profilida bir nechta joy kiritadi va turist
ulardan birini **tanlaydi**mi? Joy xaritada (koordinata) bilan bo'lishi kerakmi?

## 3. Bron oxirida kod chiqishi

**Muammo:** har qanday bron qilingandan keyin oxirida kod (masalan `LZEMMRFZZ7`, `LG…`, `LH…`) chiqib qolyapti.

**Kerak:** foydalanuvchiga ko'rinadigan joylardan bu kodni **olib tashlash**.

**Aniqlashtirish kerak:** kod faqat sayt sahifalaridan olinadimi yoki email/SMS xabarlar, admin panel va hamkor kabinetidan ham?
(Ichki ishlatish — bronni topish, to'lov — uchun bazada qoladi.)

## 4. SMS o'rniga Telegram kod

**Muammo:** "SMS bilan kiring" degan joylar bor.

**Kerak:** "SMS bilan kirish" yozilgan **hamma joyda** tekshiruv **Telegram verification code** orqali bo'lsin
(1-band bilan bir xil mexanizm). Matnlar ham shunga moslab o'zgartiriladi.

## 5. Google (Gmail) orqali kirish

**Kerak:** kirish sahifasiga **"Google orqali kirish"** imkoniyatini qo'shish (Gmail akkaunti bilan).

**Kerak bo'ladi:** Google Cloud Console'da OAuth Client ID (veb-sayt manzili bilan) — buni loyiha egasi yaratadi.

## 6. Frontend dizayni — skrinshotlar asosida

**Kerak:** foydalanuvchi `D:\lazuri\skrenshot\` papkasini yaratib, frontend qanday ko'rinishi kerakligi haqida rasmlar yuklaydi.
Frontend shu rasmlarni ko'rib chiqqan holda yoziladi.

**Holat:** rasmlar yuklanishi kutilmoqda.

---

## Bajarildi (backend, 2026-11-21)

Qabul qilingan qarorlar (aniqlashtirish savollariga javob bo'lmagani uchun — kerak bo'lsa o'zgartiriladi):

1. **Telefon.** Kod **Telegram Gateway** orqali to'g'ridan-to'g'ri raqamga yuboriladi (`TELEGRAM_CODE_BACKEND=gateway`,
   `TELEGRAM_GATEWAY_TOKEN`; dev'da `console` — kod `docker compose logs web` da). Format: faqat `+998` + 9 raqam.
   Yangi API: `POST /auth/phone-check/send-code/` → `POST /auth/phone-check/verify/` → `phone_token` (1 soat).
   Tur/gid/mehmonxona broni, agentlik arizasi, gid va mehmonxona profili, agentlik kabineti — telefon bilan birga
   `phone_token` talab qilinadi. Akkauntdagi **tasdiqlangan** raqam uchun token shart emas; tahrirlashda raqam
   o'zgarmasa ham. Sayohatchilar telefoni (ixtiyoriy) — faqat format.
2. **Uchrashuv joyi.** Tur: `meeting_point` majburiy; e'longa yuborishda xarita havolasi yoki koordinata ham shart.
   Gid: o'z kabinetida joylar ro'yxatini kiritadi (`/cabinet/guide/meeting-points/`: shahar, nom, manzil,
   koordinata — majburiy); turist bron qilganda faqat shulardan birini **tanlaydi** (`meeting_point` = id).
3. **Bron kodi** turistga boradigan email/SMS xabarlardan olib tashlandi. Hamkor (agentlik, gid, mehmonxona) va admin
   xabarlarida qoldi — ular bronni shu kod bilan topadi. API'da `code` qoldi (sahifa manzili uchun ishlatiladi).
4. **SMS → Telegram.** Telefon orqali kirish, telefon ulash va formadagi tasdiqlash — hammasi Telegram kodi.
   Bron haqidagi bildirishnoma SMS'lari (kirish emas) o'zgarmadi.
5. **Google.** `POST /auth/google/` (`credential` — Google ID token) → JWT. `GOOGLE_CLIENT_ID` bo'sh bo'lsa — o'chiq.
   `/features/` → `google_login.client_id` frontend tugmasi uchun.

**Frontend'da qilinishi kerak (hali qilinmagan):** `+998` qotirilgan maydon va "Telegram kod" tugmasi barcha
telefon formalarida, gid bronida uchrashuv joyini ro'yxatdan tanlash, gid kabinetida joylarni boshqarish,
bron kodini sahifalardan olib tashlash, "SMS" matnlari, "Google orqali kirish" tugmasi.
**Diqqat:** hozirgi frontend formalari `phone_token` yubormaydi, shuning uchun bronlar va arizalar
"Telefon raqami tasdiqlanmagan" xatosini beradi. Akkauntida tasdiqlangan telefoni bor foydalanuvchida bu xato chiqmaydi.
