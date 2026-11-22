"""Admin hisobini Environment'dan o'rnatadi: DJANGO_SUPERUSER_EMAIL + DJANGO_SUPERUSER_PASSWORD.

- Shu email bilan foydalanuvchi bo'lmasa — yaratiladi.
- Bor bo'lsa (masalan oldin Google orqali kirgan) — admin qilinadi.
- Parol har safar Environment'dagi qiymatga o'rnatiladi (almashtirish — Render'da qiymatni o'zgartirib,
  qayta deploy qilish).
Render (Shell yo'q) uchun: scripts/render-start.sh har ishga tushganda chaqiradi.
"""

import os

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = "DJANGO_SUPERUSER_EMAIL va DJANGO_SUPERUSER_PASSWORD bo'yicha admin hisobini yaratadi/yangilaydi."

    def handle(self, *args, **options):
        email = (os.environ.get("DJANGO_SUPERUSER_EMAIL") or "").strip().lower()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD") or ""
        if not email or not password:
            self.stdout.write(
                "ensure_admin: DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD berilmagan — o'tkazildi."
            )
            return
        if len(password) < 8:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD kamida 8 belgi bo'lsin.")

        user = User.objects.filter(email__iexact=email).first()
        created = user is None
        if created:
            user = User.objects.create_superuser(email=email, password=password)
        else:
            user.is_staff = user.is_superuser = user.is_active = True
            user.role = User.Role.ADMIN
            user.set_password(password)
            user.save(update_fields=["is_staff", "is_superuser", "is_active", "role", "password"])
        self.stdout.write(
            self.style.SUCCESS(f"ensure_admin: {'yaratildi' if created else 'yangilandi'} — {email}")
        )
