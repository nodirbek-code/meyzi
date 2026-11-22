"""
Sayt kontenti: savol-javob (FAQ), sahifalar (foydalanish shartlari, maxfiylik siyosati) va qo'llanmalar.

Matnlar platformaning amaldagi qoidalariga asoslangan (apps/bookings, apps/tours/policies.py, apps/guides,
apps/hotels, apps/accounts). Qoida o'zgarsa — shu yerni ham yangilang va `manage.py seed_content --force` qiling.
Sahifalar (shartlar, siyosat) — hujjat belgilash: birinchi qator — hujjat nomi, "## " — bo'lim, "1.1." — band,
"- " — ro'yxat (frontend: components/LegalDocument.tsx). Qo'llanmalar — oddiy matn, ro'yxat — "•".

Foydalanish shartlari va maxfiylik siyosati — platforma qoidalari asosidagi qoralama;
e'lon qilishdan oldin yurist ko'rib chiqishi tavsiya etiladi.
"""

SUPPORT_EMAIL = "info@meyzi.uz"
SUPPORT_PHONE = "+998 91 912 66 90"

# ---------------------------------------------------------------------------
# Savol-javob: (savol, javob). Tartib — ro'yxatdagi tartib.
# ---------------------------------------------------------------------------

FAQ = [
    (
        "Qanday ro'yxatdan o'taman?",
        "Ikki usul bor:\n"
        "• Telegram orqali — «Telegram orqali kirish» tugmasini bosing, Meyzi boti ochiladi. Botga telefon "
        "raqamingizni tugma orqali yuboring va ism-familiyangizni yozing. Bot saytga kirish havolasini beradi — "
        "uni bossangiz, saytda hisobingizga kirgan bo'lasiz.\n"
        "• Google orqali — Gmail akkauntingiz bilan bir bosishda.\n"
        "Hisob birinchi kirishda avtomatik yaratiladi, parol o'ylab topish shart emas.",
    ),
    (
        "Bot yuborgan havola ishlamayapti. Nima qilay?",
        "Havola xavfsizlik uchun 10 daqiqa amal qiladi va faqat bir marta ishlaydi. Muddati o'tgan bo'lsa, botga "
        "/start yozing — u darhol yangi havola yuboradi. Ilgari ro'yxatdan o'tgan bo'lsangiz, raqamni qayta "
        "yuborish shart emas.",
    ),
    (
        "Nega bot raqamimni faqat tugma orqali qabul qiladi?",
        "Telegram'ning «Raqamni yuborish» tugmasi raqam aynan sizniki ekanini kafolatlaydi. Shuning uchun qo'lda "
        "yozilgan yoki boshqa odamning kontakti qabul qilinmaydi — hech kim sizning raqamingiz bilan hisob ocha "
        "olmaydi. Hozircha O'zbekiston raqamlari (+998) qabul qilinadi.",
    ),
    (
        "Profilimga email qanday qo'shaman?",
        "Shaxsiy kabinet → Profil → «Email» bo'limida emailingizni yozing va «Kod yuborish»ni bosing. Emailga "
        "6 xonali kod keladi (Spam papkasini ham tekshiring). Kodni kiritsangiz, email hisobingizga tasdiqlangan "
        "holda ulanadi. Kod 10 daqiqa amal qiladi.",
    ),
    (
        "Telefon raqamimni almashtirmoqchiman.",
        "Telefon raqami hisobingizning asosiy kaliti — u Telegram bot orqali tasdiqlangan. Raqamni almashtirish "
        f"uchun qo'llab-quvvatlash xizmatiga yozing: {SUPPORT_EMAIL}.",
    ),
    (
        "Turni qanday bron qilaman?",
        "Tur sahifasida jo'nash sanasini va joylar sonini tanlang, aloqa uchun ism va telefoningizni kiriting. "
        "Joylar sizga darhol 30 daqiqaga band qilinadi — shu vaqt ichida to'lovni amalga oshiring. "
        "To'lanmasa, joylar avtomatik ravishda yana sotuvga chiqadi.",
    ),
    (
        "Bir vaqtda nechta bron qilishim mumkin?",
        "To'lanmagan bronlar bir vaqtda 3 tagacha bo'lishi mumkin. To'langan (tasdiqlangan) bronlar soni "
        "cheklanmagan.",
    ),
    (
        "Do'stlarim uchun ham bron qila olamanmi?",
        "Ha. Joylar sonini guruhingizga qarab tanlang. Xohlasangiz, sayohatchilar ro'yxatini (ism-familiyalarni) "
        "ham kiritishingiz mumkin — bu agentlikka guruhni oldindan tayyorlashda yordam beradi.",
    ),
    (
        "Bo'sh joylar va sanalarni qayerda ko'raman?",
        "Tur sahifasida kelgusi jo'nash sanalari va har bir sanada qolgan joylar soni ko'rsatiladi. "
        "Ma'lumotlar real vaqtda yangilanadi. Bosh sahifadagi sanalar tasmasidan ham kunni tanlashingiz mumkin.",
    ),
    (
        "Turlar qayerdan jo'naydi?",
        "Ko'pchilik turlar Toshkentdan jo'naydi. Uchrashuv joyi va vaqti tur sahifasida, xarita havolasi bilan "
        "ko'rsatiladi. Jo'nash vaqtidan 10–15 daqiqa oldin yetib keling.",
    ),
    (
        "Narxga nimalar kiradi?",
        "Har bir tur sahifasida «Narxga kiradi», «Narxga kirmaydi» va «O'zingiz bilan oling» ro'yxatlari bor: "
        "transport, gid, ovqat, kirish chiptalari va hokazo. Narx bir kishi uchun, so'mda ko'rsatiladi. "
        "Kunlik dasturda «o'z hisobidan» belgisi bor bandlar narxga kirmaydi.",
    ),
    (
        "Qanday to'lov usullari bor?",
        "Payme, Click va Uzum Nasiya (muddatli to'lov) orqali onlayn to'lov tez kunda ishga tushadi. "
        "Hozircha bron qilganingizdan so'ng operatorimiz siz bilan bog'lanib, to'lovni rasmiylashtiradi.",
    ),
    (
        "Bo'lib to'lash qanday ishlaydi?",
        "Uzum Nasiya orqali 12 oyga bo'lib to'lash mumkin bo'ladi. Bunda jami summa tur narxidan 44% ko'p bo'ladi "
        "va 12 ta teng oylik to'lovga bo'linadi. Oylik to'lov miqdori tur sahifasida ko'rsatiladi.",
    ),
    (
        "Narx nega o'zgarishi mumkin?",
        "Ba'zi sanalarda (bayramlar, mavsum) agentlik maxsus narx belgilashi mumkin — u sana tanlanganda "
        "ko'rsatiladi. Bron qilingan paytdagi narx qotiriladi va keyin o'zgarmaydi.",
    ),
    (
        "Bronni bekor qilsam, pul qaytariladimi?",
        "Har bir turning bekor qilish shartlari to'lovdan oldin ko'rsatiladi:\n"
        "• Bepul bekor qilish — jo'nashdan kamida 24 soat oldin bekor qilsangiz, to'liq qaytariladi.\n"
        "• Qisman qaytarish — jo'nashdan 48 soatdan ko'proq oldin bekor qilsangiz, 50% qaytariladi.\n"
        "• Qaytarilmaydi — to'langan summa qaytarilmaydi.\n"
        "Bekor qilish shaxsiy kabinetdagi «Bronlarim» bo'limidan amalga oshiriladi. Jo'nash vaqti o'tgach bronni "
        "bekor qilib bo'lmaydi.",
    ),
    (
        "Agentlik turni bekor qilsa-chi?",
        "Agar agentlik turni yoki jo'nash sanasini bekor qilsa, to'lagan pulingiz doim 100% qaytariladi — "
        "turning bekor qilish shartlaridan qat'i nazar.",
    ),
    (
        "Meyzi Coins nima?",
        "Meyzi orqali sayohat qilgan sari to'planadigan bonus ballar. Sayohatingiz yakunlangach, hisobingizga coin "
        "qo'shiladi. Coinlarni hamkorlarimizning maxsus takliflari, chegirmalar va boshqa imtiyozlarga almashtirish "
        "mumkin. Coins — pul emas: ularni naqd pulga aylantirib yoki boshqa foydalanuvchiga o'tkazib bo'lmaydi. "
        "Tizim bosqichma-bosqich ishga tushirilmoqda.",
    ),
    (
        "Meyzi Membership Card'ni qanday olaman?",
        "Meyzi Card Meyzi orqali kamida 3 ta sayohatni amalga oshirgan foydalanuvchilarga beriladi. Karta egasi "
        "maxsus a'zolik maqomiga, hamkorlar chegirmalariga va faqat karta egalari uchun takliflarga ega bo'ladi, "
        "Meyzi Coins to'plashda ham davom etadi.",
    ),
    (
        "Shaxsiy gidni qanday bron qilaman?",
        "«Gidlar» bo'limida gidni tanlang va sanani, davomiylikni (yarim kun, to'liq kun yoki 2–14 kun) va "
        "guruh hajmini ko'rsatib so'rov yuboring. Gid 24 soat ichida javob beradi. Gid qabul qilgach, to'lov "
        "qilasiz va bron tasdiqlanadi. Gidning telefon raqami to'lovdan keyin ochiladi. 5 va undan ortiq "
        "kishilik guruhlar uchun narxga ustama qo'shiladi.",
    ),
    (
        "Gid bronini bekor qilsam-chi?",
        "To'langan gid bronini bekor qilganda qaytariladigan summa qolgan vaqtga bog'liq: 48 soatdan ko'proq "
        "oldin — 100%, 24 soatdan ko'proq oldin — 50%, 12 soatdan ko'proq oldin — 25%, undan kam — qaytarilmaydi. "
        "Gid o'zi bekor qilsa yoki kelmasa, pul to'liq qaytariladi.",
    ),
    (
        "Mehmonxonani qanday bron qilaman?",
        "«Mehmonxonalar» bo'limida mehmonxona va xona turini tanlang, kirish va chiqish sanalarini, mehmonlar "
        "sonini kiriting. Bo'sh xonalar har bir kecha uchun ko'rsatiladi. Bir bronda 30 kechagacha. Xona 30 "
        "daqiqaga band qilinadi — shu vaqt ichida to'lang. Bekor qilish shartlari mehmonxona sahifasida "
        "ko'rsatiladi.",
    ),
    (
        "Sharh qanday qoldiraman?",
        "Sayohat yakunlangach, «Bronlarim» bo'limida shu bron uchun 1 dan 5 gacha baho va sharh qoldirishingiz "
        "mumkin. Bitta bronga bitta sharh. Sharhni 14 kun ichida tahrirlash mumkin. Saytda ismingiz qisqartirilgan "
        "holda ko'rsatiladi (masalan, «Aziz K.»).",
    ),
    (
        "Turni kim o'tkazadi? Agentliklar ishonchlimi?",
        "Turni sahifada ko'rsatilgan agentlik o'tkazadi. Har bir agentlik platformaga qo'shilishdan oldin "
        "tekshiriladi (STIR, litsenziya), har bir tur e'lon qilinishdan oldin moderatsiyadan o'tadi. "
        "Platformaning o'zi ham turlar tashkil qiladi. Agentlik va turlarning reytingi faqat haqiqiy "
        "sayohatchilarning sharhlaridan hisoblanadi.",
    ),
    (
        "Ma'lumotlarim xavfsizmi?",
        "Kirish tokenlari brauzerda himoyalangan cookie'da saqlanadi, tasdiqlash kodlari bazada shifrlangan "
        "(xeshlangan) holda turadi. Telefon raqamingiz faqat bron qilgan agentlik, gid yoki mehmonxonaga "
        "sayohatni tashkil qilish uchun beriladi. Batafsil — «Maxfiylik siyosati» sahifasida.",
    ),
    (
        "Men turagentlikman — qanday qo'shilaman?",
        "«Agentliklar uchun» bo'limida ariza qoldiring: agentlik nomi, mas'ul shaxs va telefon. Jamoamiz 24 soat "
        "ichida siz bilan bog'lanadi, hujjatlarni (STIR, litsenziya) tekshiradi va kabinetingizni faollashtiradi. "
        "Kabinetda turlar, jo'nash sanalari va bronlarni boshqarasiz.",
    ),
    (
        "Gid yoki mehmonxona sifatida qo'shilsam bo'ladimi?",
        "Ha. Shaxsiy kabinetda gid yoki mehmonxona profilini to'ldirib, arizani yuboring. Ma'muriyat ko'rib "
        "chiqib tasdiqlagach, profilingiz saytda ko'rinadi va bronlarni qabul qila boshlaysiz.",
    ),
]

# ---------------------------------------------------------------------------
# Sahifalar
# ---------------------------------------------------------------------------

TERMS = f"""MEYZI platformasidan foydalanish shartlari (ommaviy oferta)

Mazkur hujjat O'zbekiston Respublikasi Fuqarolik kodeksiga muvofiq ommaviy oferta hisoblanadi. Platformada ro'yxatdan o'tish yoki xizmatni bron qilish ushbu shartlarning to'liq va so'zsiz qabul qilinganini (aksept) bildiradi.

## 1. Atamalar
1.1. Platforma — meyzi.uz veb-sayti, MEYZI Telegram boti va mobil ilovasi, shuningdek ular orqali ko'rsatiladigan xizmatlar majmui.
1.2. Ma'muriyat — Platformani boshqaruvchi va uning faoliyatini ta'minlovchi shaxs.
1.3. Foydalanuvchi — Platformada ro'yxatdan o'tgan yoki undan foydalanayotgan jismoniy shaxs.
1.4. Hamkor — Platforma orqali o'z xizmatlarini taklif qiluvchi turagentlik, shaxsiy gid yoki joylashtirish vositasi (mehmonxona, mehmon uyi).
1.5. Xizmat — Hamkor yoki Ma'muriyat tomonidan Platformada taklif etiladigan tur, gid xizmati yoki joylashtirish xizmati.
1.6. Bron — Foydalanuvchining muayyan Xizmatni muayyan sana uchun band qilishi.
1.7. Bonus dasturi — Meyzi Coins bonus birliklari va Meyzi Membership Card a'zolik dasturi.

## 2. Umumiy qoidalar
2.1. Platforma Foydalanuvchi va Hamkor o'rtasida Xizmatni topish, bron qilish va to'lash uchun axborot vositachisi bo'lib xizmat qiladi.
2.2. Xizmat sahifasida Xizmatni ko'rsatuvchi shaxs aniq ko'rsatiladi. Ma'muriyatning o'zi tashkil etgan turlar alohida belgilanadi; bunday turlar bo'yicha Ma'muriyat Xizmat ko'rsatuvchi hisoblanadi.
2.3. Hamkorlar Platformaga qo'shilishdan oldin Ma'muriyat tomonidan tekshiriladi, Xizmatlar esa e'lon qilinishdan oldin moderatsiyadan o'tkaziladi.
2.4. Platformadan foydalanish uchun Foydalanuvchi 18 yoshga to'lgan bo'lishi kerak. Voyaga yetmaganlar uchun bronni ularning qonuniy vakillari rasmiylashtiradi.

## 3. Ro'yxatdan o'tish va hisob
3.1. Ro'yxatdan o'tish Telegram bot (telefon raqami Telegram orqali tasdiqlanadi) yoki Google akkaunti orqali amalga oshiriladi.
3.2. Foydalanuvchi o'zi haqida to'g'ri va dolzarb ma'lumotlarni taqdim etish majburiyatini oladi.
3.3. Foydalanuvchi o'z hisobiga kirish vositalarining (Telegram, Google akkaunti, bir martalik kirish havolalari) maxfiyligini ta'minlaydi va ular orqali amalga oshirilgan harakatlar uchun javobgar bo'ladi.
3.4. Ma'muriyat ushbu shartlarni buzgan Foydalanuvchining hisobini vaqtincha yoki butunlay bloklash huquqiga ega.

## 4. Bron qilish tartibi
4.1. Xizmat narxi O'zbekiston so'mida, bir kishi uchun ko'rsatiladi. Ayrim sanalar uchun alohida narx belgilanishi mumkin.
4.2. Bron rasmiylashtirilgach, joylar Foydalanuvchi uchun 30 (o'ttiz) daqiqaga band qilinadi. Ushbu muddatda to'lov amalga oshirilmasa, Bron avtomatik ravishda bekor qilinadi.
4.3. Bron paytida amalda bo'lgan narx va bekor qilish shartlari Bronga nisbatan qat'iy belgilanadi va keyinchalik o'zgartirilmaydi.
4.4. To'lov to'liq qabul qilingan paytdan boshlab Bron tasdiqlangan hisoblanadi.

## 5. To'lov
5.1. To'lov Platformada ko'rsatilgan to'lov tizimlari orqali amalga oshiriladi. Onlayn to'lov ishga tushgunga qadar to'lov Ma'muriyat vakili orqali rasmiylashtiriladi.
5.2. Muddatli to'lov tegishli to'lov xizmati provayderining shartlari asosida amalga oshiriladi; muddatli to'lovning umumiy summasi va oylik to'lov miqdori to'lovdan oldin ko'rsatiladi.
5.3. To'lov tizimlari bilan bog'liq munosabatlar ularning o'z qoidalari bilan tartibga solinadi.

## 6. Bronni bekor qilish va mablag'ni qaytarish
6.1. Har bir Xizmat uchun bekor qilish sharti Xizmat sahifasida ko'rsatiladi va to'lovdan oldin Foydalanuvchiga ma'lum qilinadi.
6.2. Turlar uchun quyidagi shartlardan biri qo'llaniladi:
- «Bepul bekor qilish» — jo'nash vaqtidan kamida 24 soat oldin bekor qilinganda to'langan summa to'liq qaytariladi;
- «Qisman qaytarish» — jo'nash vaqtidan 48 soatdan ko'proq oldin bekor qilinganda to'langan summaning 50 foizi qaytariladi;
- «Qaytarilmaydi» — to'langan summa qaytarilmaydi.
6.3. Jo'nash vaqti Xizmat sahifasida ko'rsatilgan sana va vaqt bo'yicha (Toshkent vaqti) aniqlanadi. Jo'nash vaqti o'tgach Bronni bekor qilishga yo'l qo'yilmaydi.
6.4. Xizmat Hamkor yoki Ma'muriyat tashabbusi bilan bekor qilingan taqdirda, to'langan summa to'liq qaytariladi.
6.5. Gid xizmatlari va joylashtirish xizmatlari uchun bekor qilish shartlari tegishli Xizmat sahifasida ko'rsatiladi.
6.6. Mablag' to'lov amalga oshirilgan usul orqali, to'lov tizimi belgilagan muddatlarda qaytariladi.

## 7. Tomonlarning huquq va majburiyatlari
7.1. Foydalanuvchi:
- Xizmat tavsifi, dasturi va shartlari bilan Bron qilishdan oldin tanishib chiqishi;
- belgilangan vaqtda uchrashuv joyida hozir bo'lishi;
- gid va tashkilotchilarning xavfsizlik bo'yicha ko'rsatmalariga rioya qilishi;
- tabiat, tarixiy-madaniy meros obyektlari va mahalliy urf-odatlarni hurmat qilishi;
- sog'lig'i bilan bog'liq cheklovlar haqida tashkilotchini oldindan xabardor qilishi shart.
7.2. Ma'muriyat:
- Platformaning uzluksiz ishlashini ta'minlash uchun oqilona choralar ko'radi;
- Foydalanuvchilarning murojaat va shikoyatlarini ko'rib chiqadi;
- shartlarni buzgan Hamkorlarni Platformadan chetlashtirish huquqiga ega.

## 8. Sharhlar
8.1. Sharhni faqat Xizmatdan foydalanib bo'lgan Foydalanuvchi qoldirishi mumkin.
8.2. Haqoratli, yolg'on, reklama mazmunidagi yoki qonunchilikka zid sharhlar Ma'muriyat tomonidan yashirilishi mumkin.

## 9. Bonus dasturi
9.1. Meyzi Coins — Platforma ichidagi bonus birliklari bo'lib, to'lov vositasi hisoblanmaydi, naqd pulga almashtirilmaydi va boshqa shaxsga o'tkazilmaydi.
9.2. Meyzi Membership Card Bonus dasturi shartlarida belgilangan talablarni bajargan Foydalanuvchiga beriladi.
9.3. Bonus dasturi shartlari Platformada e'lon qilinadi va Ma'muriyat tomonidan o'zgartirilishi mumkin.

## 10. Javobgarlik
10.1. Xizmatning sifati, dasturga muvofiqligi va xavfsizligi uchun Xizmatni ko'rsatuvchi shaxs javobgar bo'ladi.
10.2. Ma'muriyat Foydalanuvchining shartlarni buzishi, shuningdek yengib bo'lmaydigan kuch holatlari (tabiiy ofatlar, ob-havo sharoiti, davlat organlarining qarorlari va boshqalar) natijasida yuzaga kelgan oqibatlar uchun javobgar bo'lmaydi.
10.3. Yengib bo'lmaydigan kuch holatlarida Xizmat dasturi o'zgartirilishi mumkin; bunday holda Foydalanuvchi imkon qadar tezroq xabardor qilinadi.

## 11. Nizolarni hal qilish
11.1. Tomonlar o'rtasidagi nizolar muzokaralar yo'li bilan hal qilinadi. Murojaatlar Platformada ko'rsatilgan aloqa manzillari orqali yuboriladi.
11.2. Kelishuvga erishilmagan taqdirda nizo O'zbekiston Respublikasi qonunchiligida belgilangan tartibda sudda ko'rib chiqiladi.

## 12. Yakuniy qoidalar
12.1. Ma'muriyat ushbu shartlarga o'zgartirish kiritish huquqiga ega. Yangi tahrir Platformada e'lon qilingan kundan boshlab kuchga kiradi.
12.2. O'zgartirishlar kuchga kirgunga qadar rasmiylashtirilgan Bronlarga Bron paytida amalda bo'lgan shartlar qo'llaniladi.
12.3. Ushbu shartlarda nazarda tutilmagan munosabatlar O'zbekiston Respublikasi qonunchiligi bilan tartibga solinadi.

## 13. Aloqa ma'lumotlari
13.1. Elektron pochta: {SUPPORT_EMAIL}
13.2. Telefon: {SUPPORT_PHONE}
"""

PRIVACY = f"""Shaxsga doir ma'lumotlarni qayta ishlash siyosati

Mazkur siyosat «Shaxsga doir ma'lumotlar to'g'risida»gi O'zbekiston Respublikasi Qonuniga muvofiq ishlab chiqilgan bo'lib, MEYZI platformasi Foydalanuvchilarining shaxsga doir ma'lumotlarini yig'ish, qayta ishlash, saqlash va himoya qilish tartibini belgilaydi.

## 1. Umumiy qoidalar
1.1. Ushbu siyosatda ishlatiladigan atamalar Platformadan foydalanish shartlaridagi ma'nolarda qo'llaniladi.
1.2. Platformada ro'yxatdan o'tish orqali Foydalanuvchi o'zining shaxsga doir ma'lumotlarini ushbu siyosatda belgilangan maqsad va tartibda qayta ishlashga rozilik beradi.
1.3. Ma'muriyat shaxsga doir ma'lumotlarning maxfiyligini ta'minlaydi va ularni faqat qonunchilikda hamda ushbu siyosatda nazarda tutilgan hollarda uchinchi shaxslarga taqdim etadi.

## 2. Qayta ishlanadigan ma'lumotlar
2.1. Identifikatsiya va aloqa ma'lumotlari: ism, familiya, telefon raqami, elektron pochta manzili.
2.2. Tashqi xizmatlar orqali kirishda olinadigan ma'lumotlar: Telegram foydalanuvchi identifikatori; Google akkauntidagi ism va elektron pochta manzili.
2.3. Bron ma'lumotlari: tanlangan Xizmat, sana, ishtirokchilar soni va Foydalanuvchi ixtiyoriy ravishda kiritgan ishtirokchilar ro'yxati.
2.4. Foydalanuvchi qoldirgan sharhlar va baholar.
2.5. Platformaning ishlashini ta'minlash uchun zarur bo'lgan texnik ma'lumotlar.

## 3. Qayta ishlash maqsadlari
3.1. Ma'lumotlar quyidagi maqsadlarda qayta ishlanadi:
- Foydalanuvchini ro'yxatdan o'tkazish va uning hisobiga xavfsiz kirishni ta'minlash;
- Bronlarni rasmiylashtirish va Xizmat ko'rsatilishini tashkil etish;
- Bron holati, to'lov va o'zgarishlar haqida Foydalanuvchini xabardor qilish;
- Foydalanuvchilarning murojaatlarini ko'rib chiqish;
- firibgarlik va qonunbuzarliklarning oldini olish;
- Bonus dasturini yuritish.
3.2. Ma'lumotlar reklama maqsadida uchinchi shaxslarga sotilmaydi va berilmaydi.

## 4. Ma'lumotlarni uchinchi shaxslarga taqdim etish
4.1. Ma'lumotlar faqat Xizmatni ko'rsatish uchun zarur bo'lgan hajmda quyidagilarga taqdim etilishi mumkin:
- Foydalanuvchi bron qilgan Xizmatni ko'rsatuvchi Hamkorga;
- to'lovni amalga oshirish uchun to'lov tizimlari operatorlariga;
- qonunchilikda belgilangan hollarda vakolatli davlat organlariga.
4.2. Platformada ommaviy e'lon qilinadigan sharhlarda Foydalanuvchining ismi qisqartirilgan holda ko'rsatiladi; telefon raqami va elektron pochta manzili oshkor qilinmaydi.

## 5. Ma'lumotlarni himoya qilish
5.1. Ma'muriyat shaxsga doir ma'lumotlarni ruxsatsiz kirish, o'zgartirish, oshkor qilish va yo'q qilinishdan himoya qilish uchun zarur huquqiy, tashkiliy va texnik choralarni ko'radi.
5.2. Ma'lumotlarga Ma'muriyat xodimlari faqat o'z vazifalarini bajarish uchun zarur bo'lgan hajmda kirish huquqiga ega.

## 6. Cookie fayllari
6.1. Platforma faqat uning ishlashi uchun zarur bo'lgan cookie fayllaridan, jumladan Foydalanuvchi hisobiga kirgan holatni saqlash uchun foydalanadi.
6.2. Reklama va kuzatuv maqsadidagi cookie fayllaridan foydalanilmaydi.

## 7. Saqlash muddati
7.1. Hisob ma'lumotlari Foydalanuvchi hisobi faol bo'lgan davr mobaynida saqlanadi.
7.2. Bron va to'lovlarga oid ma'lumotlar qonunchilikda belgilangan muddat davomida saqlanadi.
7.3. Qayta ishlash maqsadiga erishilgach yoki rozilik qaytarib olingach, ma'lumotlar qonunchilikda belgilangan tartibda yo'q qilinadi.

## 8. Foydalanuvchining huquqlari
8.1. Foydalanuvchi quyidagi huquqlarga ega:
- o'ziga oid ma'lumotlar qayta ishlanayotgani haqida axborot olish;
- noto'g'ri yoki eskirgan ma'lumotlarni tuzatishni talab qilish;
- ma'lumotlarni qayta ishlashga berilgan rozilikni qaytarib olish;
- hisobini va unga oid ma'lumotlarni o'chirishni talab qilish (qonunchilikka ko'ra saqlanishi shart bo'lgan ma'lumotlar bundan mustasno).
8.2. Ushbu huquqlarni amalga oshirish uchun Foydalanuvchi 10-bo'limda ko'rsatilgan manzilga murojaat qiladi.

## 9. Siyosatga o'zgartirishlar kiritish
9.1. Ma'muriyat ushbu siyosatga o'zgartirish kiritish huquqiga ega. Yangi tahrir Platformada e'lon qilingan kundan boshlab kuchga kiradi.

## 10. Aloqa ma'lumotlari
10.1. Elektron pochta: {SUPPORT_EMAIL}
10.2. Telefon: {SUPPORT_PHONE}
"""

PAGES = [
    ("terms", "Foydalanish shartlari", TERMS),
    ("privacy", "Maxfiylik siyosati", PRIVACY),
]

# ---------------------------------------------------------------------------
# Qo'llanmalar (maqolalar): slug, sarlavha, qisqa mazmun, yo'nalish slugi (yoki None), matn
# ---------------------------------------------------------------------------

ARTICLES = [
    (
        "togga-sayohatga-nimalar-olish-kerak",
        "Tog'ga sayohatga nimalar olish kerak: to'liq ro'yxat",
        "Bir kunlik piyoda sayohatdan tortib ko'p kunlik ekspeditsiyagacha — ryukzakka nimani solish va nimani "
        "uyda qoldirish kerakligi haqida amaliy ro'yxat.",
        None,
        """Tog'da ob-havo bir necha soat ichida o'zgaradi: ertalab quyosh charaqlab tursa, tushdan keyin shamol va yomg'ir boshlanishi mumkin. To'g'ri tayyorgarlik sayohatni qulay va xavfsiz qiladi.

Kiyim: "qatlamlar" qoidasi
• Ichki qatlam — ter o'tkazadigan sport futbolka (paxta emas: paxta terni ushlab qoladi va sovuq qiladi).
• O'rta qatlam — yengil flis yoki jun kofta.
• Tashqi qatlam — shamol va yomg'ir o'tkazmaydigan kurtka.
• Qulay shim (jinsi emas), almashtirish uchun qo'shimcha paypoq.
• Bosh kiyim: yozda — quyoshdan himoya qiluvchi kepka yoki panama, kuz-qishda — issiq shapka.

Poyabzal
• Tagi qalin, bo'g'imni ushlab turadigan trekking poyabzali yoki krossovka.
• Yangi poyabzalni sayohatdan oldin bir necha kun kiyib, oyoqqa moslang — yangi poyabzal oyoqni ishqalaydi.

Ryukzak (20–30 litr bir kunlik sayohat uchun)
• Suv: kishi boshiga kamida 1,5–2 litr.
• Yengil ovqat: yong'oq, quritilgan mevalar, shokolad, non.
• Quyoshdan himoya kremi va quyosh ko'zoynagi — tog'da quyosh shaharga qaraganda kuchliroq.
• Kichik dori qutisi: plastir, bint, og'riq qoldiruvchi, shaxsiy dorilaringiz.
• Zaryadlangan telefon va powerbank.
• Shaxsiy hujjat (pasport yoki ID karta).
• Axlat uchun paket — tog'da hech narsa qoldirmaymiz.

Ko'p kunlik sayohatda qo'shimcha
• Uxlash xaltasi va gilamcha (agar tashkilotchi bermasa — tur sahifasidagi «Narxga kiradi» ro'yxatini tekshiring).
• Fonar (bosh fonari qulayroq).
• Gigiyena vositalari va tez quriydigan sochiq.
• Issiq kiyim — tog'da tunlar yozda ham salqin bo'ladi.

Nimani olmaslik kerak
• Og'ir va keraksiz narsalar — har bir ortiqcha kilogramm tepalikda seziladi.
• Qimmatbaho zargarlik buyumlari.

Maslahat: har bir tur sahifasida «O'zingiz bilan oling» ro'yxati bor — tashkilotchi aynan shu marshrut uchun nima kerakligini yozib qo'ygan. Sayohat oldidan uni albatta o'qing.
""",
    ),
    (
        "chimyon-va-chorvoq-hafta-oxiri",
        "Chimyon va Chorvoq: Toshkentdan hafta oxiri sayohati",
        "Toshkentdan bir-ikki soatlik yo'lda tog' havosi, ko'l bo'yi va chang'i yo'laklari. Qachon borish, "
        "nima qilish va nimalarga e'tibor berish kerak.",
        "chimyon",
        """Toshkentdan bir-ikki soatlik yo'l — va siz tog'lar bag'ridasiz. Chimyon va Chorvoq poytaxt aholisining eng sevimli dam olish maskanlari bo'lib, hafta oxiri sayohati uchun juda qulay.

Chimyon
Chimyon Toshkent viloyatida, G'arbiy Tyan-Shan tog'larining Chotqol tizmasida joylashgan. Bu yerda:
• Yozda — piyoda sayohatlar, tog' cho'qqilariga chiqish, sharsharalarga yurish.
• Qishda — chang'i va snoubord. Yo'laklar boshlovchilar uchun ham, tajribalilar uchun ham bor.
• Yil davomida — kanat yo'li orqali yuqoriga ko'tarilib, atrofdagi tog'lar manzarasini tomosha qilish.

Chorvoq suv ombori
Chimyondan uncha uzoq bo'lmagan Chorvoq — tog'lar orasidagi katta, moviy suv havzasi. Yozda bu yerda:
• Qirg'oqda dam olish va suzish (faqat ruxsat etilgan joylarda).
• Qayiq va suv sporti.
• Atrofdagi tepaliklarga yurish va kun botishini tomosha qilish.

Qachon borish yaxshi
• May–iyun va sentyabr–oktyabr — piyoda sayohatlar uchun eng qulay: havo iliq, issiq emas.
• Iyul–avgust — ko'l bo'yida dam olish mavsumi, ammo hafta oxirida odam ko'p bo'ladi.
• Dekabr–mart — chang'i mavsumi (qor holatiga bog'liq).

Maslahatlar
• Hafta oxiri yo'llar gavjum bo'ladi — ertaroq jo'nash vaqtni tejaydi. Guruh turlarida transport va marshrut tashkilotchi zimmasida.
• Tog'da harorat shahardagidan bir necha daraja past — yozda ham yengil kurtka oling.
• Quyosh kremi shart: balandlikda quyosh tezroq kuydiradi.
• Suvda xavfsizlik qoidalariga amal qiling: Chorvoqda suv chuqur va sovuq, faqat belgilangan joylarda suzing.

MEYZI'da Chimyon va Chorvoq yo'nalishidagi turlarni sanalar bo'yicha solishtirib, onlayn bron qilishingiz mumkin. Joylar 30 daqiqaga siz uchun band qilinadi.
""",
    ),
    (
        "ipak-yoli-samarqand-buxoro-xiva",
        "Ipak yo'li shaharlari: Samarqand, Buxoro va Xivaga birinchi safar",
        "Ko'k gumbazlar, qadimiy madrasalar va tor ko'chalar. Uch shaharni qanday rejalashtirish, nimani "
        "albatta ko'rish va qaysi mavsumni tanlash haqida.",
        "samarqand",
        """Samarqand, Buxoro va Xiva — Buyuk Ipak yo'lining durdonalari. Uchala shaharning tarixiy markazlari YUNESKO Butunjahon merosi ro'yxatiga kiritilgan. Agar O'zbekistonni endi kashf etayotgan bo'lsangiz, aynan shu yerdan boshlang.

Samarqand
• Registon maydoni — uchta ulug'vor madrasa bir maydonda. Kechqurun yoritilgan Registon alohida go'zal.
• Go'ri Amir — Amir Temur maqbarasi.
• Shohi Zinda — moviy koshinlarga burkangan maqbaralar ko'chasi.
• Bibixonim masjidi va yonidagi Siyob bozori — non, quruq meva va shirinliklar uchun.
Toshkentdan Samarqandga «Afrosiyob» tezyurar poyezdida bir necha soatda yetib borish mumkin.

Buxoro
Buxoro — "ochiq osmon ostidagi muzey". Tarixiy markaz piyoda aylanish uchun juda qulay.
• Poi Kalon majmuasi va Minorai Kalon.
• Ark qal'asi.
• Labi Hovuz — qadimiy hovuz bo'yida choy ichib dam olish.
• Savdo gumbazlari — hunarmandlar do'konlari.

Xiva
Xivaning Ichan Qal'asi — devorlar bilan o'ralgan butun bir qadimiy shahar. Kechqurun, sayyohlar kamayganda, devor ustidan kun botishini tomosha qiling.

Qanday rejalashtirish kerak
• Uchala shahar uchun kamida 5–7 kun ajrating: Samarqand — 2 kun, Buxoro — 2 kun, Xiva — 1–2 kun.
• Shaharlar orasida poyezd, avtobus yoki ichki reyslar bor. Guruh turlarida barcha ko'chishlar tashkil qilingan bo'ladi.
• Eng qulay mavsum — bahor (aprel–may) va kuz (sentyabr–oktyabr). Yozda havo juda issiq bo'ladi, shuning uchun ekskursiyalarni ertalab va kechqurun rejalashtiring.

Odob-axloq
• Masjid va maqbaralarga kirishda yelka va tizzalarni yopadigan kiyim kiying.
• Odamlarni suratga olishdan oldin ruxsat so'rang.
• Bozorda savdolashish odatiy hol — samimiy va xushmuomala bo'ling.

MEYZI'da Ipak yo'li shaharlari bo'ylab ko'p kunlik turlarni topishingiz yoki har bir shaharda shaxsiy gid bron qilishingiz mumkin.
""",
    ),
    (
        "meyzida-turni-qanday-bron-qilish",
        "MEYZI'da turni qanday bron qilish: qadamma-qadam",
        "Ro'yxatdan o'tishdan sayohat kunigacha — bron, to'lov, bekor qilish va sharh qoldirish qanday ishlaydi.",
        None,
        """MEYZI'da turni topish va bron qilish bir necha daqiqa oladi. Mana butun jarayon qadamma-qadam.

1. Ro'yxatdan o'ting
«Telegram orqali kirish» tugmasini bosing — Meyzi boti ochiladi. Telefon raqamingizni tugma orqali yuboring, ism-familiyangizni yozing va bot yuborgan havolani bosing. Yoki Google akkauntingiz bilan kiring. Parol o'ylab topish shart emas.

2. Turni tanlang
Bosh sahifadagi qidiruv, toifalar (Tog', Madaniy, Sarguzasht va boshqalar) yoki yo'nalishlar orqali turni toping. Tur sahifasida quyidagilarni albatta o'qing:
• Kunlik dastur.
• «Narxga kiradi» va «Narxga kirmaydi» ro'yxatlari.
• «O'zingiz bilan oling» ro'yxati.
• Uchrashuv joyi va jo'nash vaqti.
• Bekor qilish sharti.
• Boshqa sayohatchilarning sharhlari.

3. Sana va joylarni tanlang
Kelgusi jo'nash sanalari va har bir sanada qolgan joylar soni ko'rsatiladi. Joylar sonini tanlang va aloqa ma'lumotlarini kiriting. Xohlasangiz, sayohatchilar ro'yxatini ham qo'shing.

4. 30 daqiqa ichida to'lang
Bron qilinishi bilan joylar siz uchun 30 daqiqaga band qilinadi. Shu vaqt ichida to'lovni amalga oshiring — aks holda bron avtomatik bekor bo'ladi va joylar boshqalarga o'tadi. To'lov qabul qilingach, bron darhol tasdiqlanadi.

5. Sayohatga tayyorlaning
Tasdiqlangan bron «Bronlarim» bo'limida turadi: sana, uchrashuv joyi, sayohatchilar. Jo'nash kuni uchrashuv joyiga 10–15 daqiqa oldin yetib keling.

6. Rejalar o'zgardimi?
Bronni «Bronlarim» bo'limidan bekor qilishingiz mumkin. Qancha qaytarilishi turning bekor qilish shartiga bog'liq:
• Bepul bekor qilish — jo'nashdan kamida 24 soat oldin — to'liq.
• Qisman qaytarish — jo'nashdan 48 soatdan ko'proq oldin — 50%.
• Qaytarilmaydi — qaytarilmaydi.
Agentlik turni bekor qilsa, pulingiz doim to'liq qaytariladi.

7. Sharh qoldiring va coin to'plang
Sayohatdan keyin 1–5 baho va sharh qoldiring — bu boshqa sayohatchilarga to'g'ri tanlov qilishga yordam beradi. Har bir yakunlangan sayohat sizga Meyzi Coins olib keladi, 3 ta sayohatdan keyin esa Meyzi Membership Card'ga ega bo'lasiz.
""",
    ),
    (
        "meyzi-coins-va-membership-card",
        "Meyzi Coins va Membership Card: sayohat qiling — imtiyozlarga ega bo'ling",
        "Bonus ballar qanday to'planadi, ularni nimaga almashtirish mumkin va Meyzi Card egalari qanday "
        "imtiyozlarga ega bo'ladi.",
        None,
        """MEYZI'da har bir sayohat nafaqat yangi taassurot, balki yangi imkoniyat ham olib keladi. Buning uchun ikkita dastur bor: Meyzi Coins va Meyzi Membership Card.

Meyzi Coins
Meyzi Coins — Meyzi orqali sayohat qilgan sari to'planadigan bonus ballar.
1. Sayohat qiling — MEYZI orqali tur tanlang va bron qiling.
2. Coin to'plang — sayohatingiz yakunlangach, hisobingizga coin qo'shiladi.
3. Mukofotlarga ega bo'ling — yig'ilgan coinlarni hamkorlarimizning maxsus takliflari, chegirmalar va boshqa imtiyozlarga almashtiring.

Muhim: Coins — pul emas, balki platforma ichidagi bonus birliklari. Ularni naqd pulga aylantirib yoki boshqa foydalanuvchiga o'tkazib bo'lmaydi.

Meyzi Membership Card
Meyzi Card — faol sayohatchilar uchun maxsus a'zolik kartasi.
1. A'zolikni qo'lga kiriting — karta MEYZI orqali kamida 3 ta sayohat qilgan foydalanuvchilarga beriladi.
2. Maxsus maqomga ega bo'ling — karta egasi Meyzi hamjamiyatining faol a'zosi hisoblanadi.
3. Ko'proq imkoniyatlardan foydalaning — maxsus takliflar, hamkorlar chegirmalari va boshqa a'zolik imtiyozlari.
4. Coins to'plashda davom eting — har bir sayohat orqali Meyzi Coins yig'ishda davom etasiz.

Meyzi Card afzalliklari
• Maxsus a'zolik maqomi.
• Meyzi Coins bonus tizimi.
• Hamkorlardan maxsus chegirmalar.
• Faqat karta egalariga mo'ljallangan takliflar.

Meyzi Card — bu shunchaki karta emas, bu ko'proq sayohat qiladiganlar uchun alohida imkoniyatlar dunyosi.

Dasturlar bosqichma-bosqich ishga tushirilmoqda. Yangiliklar va hamkorlar takliflari haqida saytda xabar beramiz.
""",
    ),
    (
        "sayohatda-xavfsizlik",
        "Sayohatda xavfsizlik: tog'da, issiqda va yo'lda",
        "Issiq urishi, tog'da adashish, suvda xavf — oddiy qoidalar bilan ularning oldini olish mumkin. "
        "Har bir sayohatchi bilishi kerak bo'lgan maslahatlar.",
        None,
        """Yaxshi sayohat — xavfsiz sayohat. Quyidagi oddiy qoidalar ko'pchilik muammolarning oldini oladi.

Issiq va quyosh
O'zbekistonda yozda harorat juda yuqori bo'ladi.
• Kun davomida suvni oz-ozdan, tez-tez iching — chanqashni kutmang.
• Eng issiq soatlarda (taxminan 12:00–16:00) soyada bo'ling, ekskursiyalarni ertalab va kechqurunga qoldiring.
• Bosh kiyim, quyosh ko'zoynagi va quyosh kremidan foydalaning.
• Bosh aylanishi, ko'ngil aynishi yoki kuchli holsizlik — issiq urishi belgilari bo'lishi mumkin. Darhol soyaga o'ting, suv iching va gidga xabar bering.

Tog'da
• Guruhdan ajralmang va gid ko'rsatgan yo'ldan chiqmang.
• Sizni qiynayotgan narsa bo'lsa (oyoq og'rig'i, nafas qisishi, bosh og'rig'i) — darhol gidga ayting. Bu zaiflik emas, xavfsizlik.
• Ob-havo yomonlashsa, marshrutni o'zgartirish yoki qaytish to'g'risidagi gid qaroriga bo'ysunining.
• Telefoningizni zaryadlab oling, ammo tog'da aloqa har doim ham bo'lmasligini yodda tuting.

Suvda
• Faqat ruxsat etilgan joylarda suzing. Tog' daryolari va suv omborlarida suv sovuq, oqim kuchli bo'lishi mumkin.
• Spirtli ichimlik ichgandan keyin suvga tushmang.
• Qayiqda qutqaruv kamzulini kiying.

Yo'lda
• Hujjatlaringiz (pasport yoki ID karta) har doim yoningizda bo'lsin.
• Qimmatbaho narsalarni ko'z-ko'z qilmang, pulni bir necha joyga bo'lib saqlang.
• Faqat tekshirilgan tashkilotchilar bilan sayohat qiling. MEYZI'dagi barcha agentliklar platformaga qo'shilishdan oldin tekshiriladi.

Sog'liq
• Surunkali kasalliklaringiz bo'lsa, kerakli dorilarni yetarli miqdorda oling va tashkilotchini oldindan xabardor qiling.
• Murakkab tog' marshrutlariga chiqishdan oldin jismoniy tayyorgarligingizni xolis baholang — tur sahifasidagi tavsifni diqqat bilan o'qing.

Favqulodda holatlar
O'zbekistonda favqulodda xizmatlar raqamlari: 101 — yong'in xavfsizligi, 102 — politsiya, 103 — tez tibbiy yordam. Telefoningizga gid va tashkilotchining raqamlarini ham yozib qo'ying.
""",
    ),
]
