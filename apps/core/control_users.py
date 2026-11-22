"""/control → Foydalanuvchilar: admin ko'radi, bloklaydi va ishchi rolini beradi.

Admin foydalanuvchini O'CHIRA OLMAYDI va uning ma'lumotlarini (ism, email, telefon, rol) O'ZGARTIRA OLMAYDI —
bularni foydalanuvchining o'zi o'zgartiradi. Ruxsat etilgan amallar:
- bloklash / blokdan chiqarish (`is_active`) — bloklangan foydalanuvchi saytga kira olmaydi;
- ishchi qilish: admin paneliga kirish (`is_staff`) va mas'ul sohasi (`staff_area`).
Har bir amal admin tarixiga yoziladi.
"""

from django.contrib.admin.models import CHANGE, LogEntry
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .control import AREA_TITLE, IsMainAdmin

MEMBERSHIP_TRIPS = 3  # Meyzi Membership Card — 3 ta yakunlangan sayohatdan keyin


def _stats(qs, statuses_done=("completed",)) -> dict:
    agg = qs.aggregate(total=Count("id"), done=Count("id", filter=Q(status__in=statuses_done)))
    return {"total": agg["total"], "completed": agg["done"]}


def user_profile(u) -> dict:
    from apps.agencies.models import AgencyMember
    from apps.guides.models import GuideProfile
    from apps.hotels.models import HotelMember

    tours = _stats(u.bookings.all())
    hotels = _stats(u.hotel_bookings.all())
    guides = _stats(u.guide_bookings.all())
    completed = tours["completed"] + hotels["completed"] + guides["completed"]

    partner = []
    for m in AgencyMember.objects.filter(user=u).select_related("agency"):
        partner.append({"kind": "Turagentlik", "name": m.agency.name, "role": m.get_role_display()})
    for m in HotelMember.objects.filter(user=u).select_related("hotel"):
        partner.append({"kind": "Mehmonxona", "name": m.hotel.name, "role": m.get_role_display()})
    g = GuideProfile.objects.filter(user=u).first()
    if g:
        partner.append({"kind": "Gid", "name": g.display_name, "role": g.get_status_display()})

    area = getattr(u, "staff_area", "")
    return {
        "id": u.pk,
        "full_name": u.full_name or "",
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "email_verified": u.email_verified,
        "phone": u.phone,
        "phone_verified": u.phone_verified,
        "role": u.role,
        "role_display": u.get_role_display(),
        "language": u.get_language_display(),
        "date_joined": u.date_joined,
        "last_login": u.last_login,
        "is_active": u.is_active,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
        "staff_area": area,
        "staff_title": (AREA_TITLE["admin"] if not area else AREA_TITLE.get(area, area))
        if u.is_staff
        else "",
        "telegram_linked": bool(u.telegram_id),
        "google_linked": bool(u.google_sub),
        "has_password": u.has_usable_password(),
        "partner": partner,
        "bookings": {"tours": tours, "hotels": hotels, "guides": guides},
        "completed_trips": completed,
        "membership_card": completed >= MEMBERSHIP_TRIPS,
        "membership_left": max(MEMBERSHIP_TRIPS - completed, 0),
        # Meyzi Coins balansi hali yo'q (bonus tizimi yoqilmagan) — faqat sayohatlar hisobi ko'rsatiladi
        "coins": None,
    }


def _log(request, obj, message: str) -> None:
    LogEntry.objects.log_actions(
        user_id=request.user.pk,
        queryset=[obj],
        action_flag=CHANGE,
        change_message=message,
        single_object=True,
    )


class _Admin(APIView):
    permission_classes = [IsMainAdmin]


class ControlUserView(_Admin):
    """Foydalanuvchi ma'lumotlari — faqat ko'rish."""

    @extend_schema(responses={200: dict})
    def get(self, request, pk):
        from apps.accounts.models import User

        u = get_object_or_404(User, pk=pk)
        history = [
            {"user": e.user.full_name or e.user.email, "message": e.get_change_message(), "at": e.action_time}
            for e in LogEntry.objects.filter(
                content_type__app_label="accounts", content_type__model="user", object_id=str(u.pk)
            )
            .select_related("user")
            .order_by("-action_time")[:20]
        ]
        return Response({**user_profile(u), "is_me": u.pk == request.user.pk, "history": history})


class BlockSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


class ControlUserBlockView(_Admin):
    """POST .../block | unblock — bloklangan foydalanuvchi saytga kira olmaydi (ma'lumotlari saqlanadi)."""

    @extend_schema(request=BlockSerializer, responses={200: dict})
    def post(self, request, pk, action):
        from apps.accounts.models import User

        u = get_object_or_404(User, pk=pk)
        if action not in ("block", "unblock"):
            raise ValidationError({"detail": "Noma'lum amal."})
        if u.pk == request.user.pk:
            raise ValidationError({"detail": "O'zingizni bloklay olmaysiz."})
        if u.is_superuser and action == "block":
            raise ValidationError({"detail": "Asosiy adminni bloklab bo'lmaydi."})
        ser = BlockSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reason = ser.validated_data["reason"].strip()
        u.is_active = action == "unblock"
        u.save(update_fields=["is_active"])
        if action == "block":
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

            # faol sessiyalari darhol tugaydi
            for t in OutstandingToken.objects.filter(user=u):
                BlacklistedToken.objects.get_or_create(token=t)
        _log(
            request,
            u,
            ("🚫 Bloklandi" if action == "block" else "✅ Blokdan chiqarildi")
            + (f": {reason}" if reason else ""),
        )
        return Response({"is_active": u.is_active})


class StaffSerializer(serializers.Serializer):
    is_staff = serializers.BooleanField()
    staff_area = serializers.ChoiceField(choices=["", "hotels", "guides"], required=False, default="")


class ControlUserStaffView(_Admin):
    """Ishchi qilish: admin paneliga kirish va mas'ul sohasi (bo'sh — asosiy admin)."""

    @extend_schema(request=StaffSerializer, responses={200: dict})
    def post(self, request, pk):
        from apps.accounts.models import User

        u = get_object_or_404(User, pk=pk)
        if u.pk == request.user.pk:
            raise ValidationError({"detail": "O'z huquqlaringizni o'zgartira olmaysiz."})
        if u.is_superuser:
            raise ValidationError({"detail": "Asosiy admin (superuser) huquqlari bu yerda o'zgarmaydi."})
        ser = StaffSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        u.is_staff = ser.validated_data["is_staff"]
        u.staff_area = ser.validated_data["staff_area"] if u.is_staff else ""
        u.save(update_fields=["is_staff", "staff_area"])
        title = (
            (AREA_TITLE["admin"] if not u.staff_area else AREA_TITLE[u.staff_area])
            if u.is_staff
            else "oddiy foydalanuvchi"
        )
        _log(request, u, f"🛡 Huquq: {title}")
        return Response({"is_staff": u.is_staff, "staff_area": u.staff_area})
