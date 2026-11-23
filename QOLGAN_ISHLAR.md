# Qolgan ishlar

Oxirgi yangilanish: 2026-11-23. Ertaga shu ro'yxatdan davom etamiz.

## Ertaga — birinchi navbatda

### 1. Render: deploy va Cloudinary tekshiruvi
- [ ] Render → **meyzi-api → Logs**: deploy boshida quyidagilar chiqishi kerak:
  - `[env] CLOUDINARY_URL: BOR`
  - `[storage] CloudinaryStorage - OK: fayllar Cloudinary da saqlanadi`
  - `inventory: +N jo'nash sanasi, +N xona turi, +N uchrashuv joyi`
- [ ] `DIQQAT: server diski` chiqsa — `CLOUDINARY_URL` **meyzi-api** (meyzi-web emas) Environment'ida yo'q yoki
  noto'g'ri (`cloudinary://...` bilan boshlansin, oldida `CLOUDINARY_URL=` yozilmasin).
- [ ] Bitta rasm yuklab, havolasi `https://res.cloudinary.com/...` bilan boshlanishini tekshirish.

### 2. Haftaning barcha kunlari — tekshirish
- [ ] Saytda `/tours` sana tasmasi: dushanbadan yakshanbagacha har kuni turlar bo'lishi kerak
  (`fill_inventory` deployda o'zi to'ldiradi: 1 kunlik tur — haftada 5 kun, 2 kunlik — 2, uzun — 1 marta).
- [ ] Mehmonxonalar: xona turlari paydo bo'lganini va istalgan kunga bron qilish mumkinligini tekshirish.
- [ ] Gidlar: har bir gidda uchrashuv joyi borligini va istalgan kunga so'rov yuborish mumkinligini tekshirish.

### 3. Render'dagi 88 ta turni yangi mantiqqa o'tkazish
Render'ga eski turlar fayli yuklangan. Unda gid narxi (`guide_price_uzs`) yo'q va «Narxga kiradi» ro'yxatida
«Gid xizmati» deb yozilgan. Yangi mantiq: **sayohat yo'lboshchisi** narxga kiradi, **professional gid** esa ixtiyoriy.
- [ ] Qaror qilish kerak — qaysi yo'l bilan:
  - **A)** Excel orqali **mavjud yozuvni yangilash** (slug bo'yicha update) importini qo'shish va yangi
    `tayyor turlar exsel.xlsx` ni qayta yuklash. Tavsiya etiladi — keyin ham asqatadi.
  - **B)** Eski 85 ta turni o'chirib, yangi fayldan qayta yuklash (bronlari bo'lmasa).
- [ ] Shundan keyin tur sahifasida «Professional gid kerak (+300 000 so'm)» tanlovi chiqishini tekshirish.

### 4. Rasm va videolar (ZIP)
- [ ] `/control → Media (ZIP)` orqali yuklash. Arxivlarni bo'limlar bo'yicha bo'lish (har biri ≤ 100 MB):
  `turlar.zip`, `mehmonxonalar.zip`, `joylar.zip`, `gidlar.zip`, `agentliklar.zip`, `yonalishlar.zip`.
- [ ] Papka nomlari — yozuvning slug'i yoki nomi (Excel fayllaridagi «Slug» ustuni).
- [ ] Rasmlar: gorizontal, kengligi **≥ 1920 px** (hero uchun), Google'dagi kichik rasmlar emas.
- [ ] Yo'nalishlardan 3–5 tasiga «Tavsiya etiladi» belgisi — bosh sahifa hero slayderi shulardan.
- [ ] Yuklash hisobotidagi «biriktirilmagan» fayllarni ko'rib chiqish.

## Keyingi ishlar

- [ ] **Yangi viloyatlar uchun mahalliy gidlar**: gidlar faylida Andijon, Farg'ona, Namangan, Navoiy,
  Shahrisabz, Termiz, Guliston yo'q — u yerdagi turlarni Toshkentdan kuzatib boruvchi gidlar olib boradi.
  Gidlar fayliga shu shaharlarni qo'shish yoki yangi gidlar.
- [ ] **Diqqatga sazovor joylar**: ish vaqti va kirish narxlari taxminiy — asosiylarini tekshirib to'g'rilash.
- [ ] **Agentlik kabineti**: tur tahrirlash sahifasiga (TourEditor) gidlar va gid narxi maydonlarini qo'shish
  (API tayyor: `guides`, `guide_price_uzs`; UI hali yo'q).
- [ ] **Gidga bildirishnoma**: turist turda gidni tanlasa — gidga SMS/email (hozir faqat kabinetda ko'rinadi).
- [ ] **To'lov** (Payme, Click, Uzum Nasiya) — shartnomalar tuzilgach; hozir «Tez kunda».
- [ ] **Testlar Postgres'da**: lokal `meyzi` foydalanuvchisiga `ALTER ROLE meyzi CREATEDB;` (hozir SQLite'da).
- [ ] **Frontend ESLint** sozlanmagan (`next lint` savol so'raydi) — sozlash.
- [ ] `drf-spectacular` ogohlantirishlari (5 ta, eski): `ControlCertificateView`, operationId to'qnashuvlari.
- [ ] `tayyor exsel.xlsx` (agentliklar) nomini `tayyor agentliklar exsel.xlsx` ga o'zgartirish (chalkashmaslik uchun).

## Bugun qilinganlar (2026-11-23)

- Excel import: yo'nalishlar, diqqatga sazovor joylar, agentliklar, gidlar, mehmonxonalar, turlar
  (tur: gidlar, mehmonxonalar, kunlik dastur, jo'nash sanalari; o'tgan sanalar tashlab yuboriladi).
- Fayllar Cloudinary'da (`CLOUDINARY_URL` bo'lsa); gid sertifikatlari — yopiq (authenticated).
- Bosh sahifa: yo'nalishlar rasmlari almashib turadigan hero; rasmlar ustidagi yashil qoplama yengillashtirildi.
- Tur toifalari 4 → 8 (Tarix, Gastronomiya, Hunarmandchilik, Ziyorat, Tog', Tabiat, Sarguzasht, Qisqa sayohat).
- Turlar: **yo'lboshchi doim narxda, professional gid ixtiyoriy** (guruh uchun bir marta, turist o'zi tanlaydi,
  bandlik tekshiriladi, kontaktlar to'lovdan keyin); gid kabinetida «Turlardagi bronlarim»;
  filtrlar: gid, mehmonxona, gid tili.
- `/control → Media (ZIP)`: rasm/videolarni papka nomi bo'yicha ommaviy biriktirish (fonda, takrorsiz).
- `fill_inventory`: har deployda platforma turlariga haftaning barcha kunlariga sanalar, xonasiz
  mehmonxonalarga xona turlari, gidlarga uchrashuv joylari.
- Arizalarni Excel orqali yuklash qo'shildi va **olib tashlandi** (arizalar faqat saytdagi formadan).
- `.gitignore` tuzatildi: `media/` qoidasi frontend sahifalarini ham yashirgan edi
  (`/cabinet/hotel/media` Render'da yo'q edi — endi bor).

### Ish stolidagi Excel fayllar (yuklash tartibi)
1. `tayyor yonalishlar exsel.xlsx` — Yo'nalishlar (7)
2. `tayyor diqqatga sazovor joylar exsel.xlsx` — Diqqatga sazovor joylar (70)
3. `tayyor exsel.xlsx` — Agentliklar (40)
4. `tayyor gidlar exsel.xlsx` — Gidlar (60)
5. `tayyor mehmonxonalar exsel.xlsx` — Mehmonxonalar (65)
6. `tayyor turlar exsel.xlsx` — Turlar (85; yangi versiya: har kuni sanalar, ixtiyoriy gid narxi)

`tayyor ... arizalari exsel.xlsx` (3 ta) — endi yuklanmaydi (mexanizm olib tashlandi), kerak bo'lmasa o'chirish mumkin.
