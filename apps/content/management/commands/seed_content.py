from django.core.management.base import BaseCommand

from apps.content.models import FaqItem

# Platformaning amaldagi qoidalari asosida (apps/bookings, apps/tours/policies.py).
FAQ = [
    (
        "Turni qanday bron qilaman?",
        "Tur sahifasida jo'nash sanasi va joylar sonini tanlang, aloqa uchun ism va telefoningizni kiriting. "
        "Joylar sizga darhol 30 daqiqaga band qilinadi — shu vaqt ichida to'lovni amalga oshiring. "
        "To'lanmasa, joylar avtomatik ravishda yana sotuvga chiqadi.",
    ),
    (
        "Qanday to'lov usullari bor?",
        "Payme, Click va Uzum Nasiya (muddatli to'lov) orqali to'lov tez kunda ishga tushadi.",
    ),
    (
        "Narxga nimalar kiradi?",
        "Har bir tur sahifasida «Narxga kiradi» va «Narxga kirmaydi» ro'yxatlari bor: transport, gid, ovqat, "
        "kirish chiptalari va hokazo. Narx bir kishi uchun, so'mda ko'rsatiladi.",
    ),
    (
        "Bronni bekor qilsam, pul qaytariladimi?",
        "Har bir turning bekor qilish shartlari to'lovdan oldin ko'rsatiladi:\n"
        "• Bepul bekor qilish — jo'nashdan kamida 24 soat oldin bekor qilsangiz, to'liq qaytariladi.\n"
        "• Qisman qaytarish — jo'nashdan 48 soatdan ko'proq oldin bekor qilsangiz, 50% qaytariladi.\n"
        "• Qaytarilmaydi — to'langan summa qaytarilmaydi.\n"
        "Agar turni agentlik bekor qilsa, pul doim to'liq qaytariladi. "
        "Bekor qilish shaxsiy kabinetdagi «Bronlarim» bo'limidan amalga oshiriladi.",
    ),
    (
        "Turni kim o'tkazadi?",
        "Turni sahifada ko'rsatilgan agentlik o'tkazadi. Barcha agentliklar platformaga qo'shilishdan oldin "
        "tekshiriladi. Platformaning o'zi ham turlar tashkil qiladi.",
    ),
    (
        "Bo'sh joylar va sanalarni qayerda ko'raman?",
        "Tur sahifasida kelgusi jo'nash sanalari va har bir sanada qolgan joylar soni ko'rsatiladi. "
        "Ma'lumotlar real vaqtda yangilanadi.",
    ),
    (
        "Turlar qayerdan jo'naydi?",
        "Ko'pchilik turlar Toshkentdan jo'naydi. "
        "Uchrashuv joyi va vaqti tur sahifasida, xarita havolasi bilan ko'rsatiladi.",
    ),
    (
        "Sharh qanday qoldiraman?",
        "Sayohat yakunlangach, «Bronlarim» bo'limida shu bron uchun "
        "1 dan 5 gacha baho va sharh qoldirishingiz mumkin. Sharhni 14 kun ichida tahrirlash mumkin.",
    ),
    (
        "Men turagentlikman — qanday qo'shilaman?",
        "«Agentliklar uchun» bo'limida ariza qoldiring: agentlik nomi, mas'ul shaxs va telefon. "
        "Jamoamiz siz bilan bog'lanadi, hujjatlarni tekshiradi va kabinetingizni faollashtiradi.",
    ),
]


class Command(BaseCommand):
    help = "Savol-javoblarni (FAQ) yuklaydi. Qayta ishga tushirish xavfsiz — mavjud savollar yangilanadi."

    def handle(self, *args, **options):
        created = 0
        for order, (question, answer) in enumerate(FAQ, start=1):
            _, is_new = FaqItem.objects.update_or_create(
                question=question, defaults={"answer": answer, "sort_order": order, "is_active": True}
            )
            created += is_new
        self.stdout.write(self.style.SUCCESS(f"FAQ: {len(FAQ)} ta savol ({created} ta yangi)."))
