from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from apps.core.admin_moderation import PartnerDataReadOnlyMixin, ReadOnlyInline, return_with_note
from apps.notifications import user_events

from . import services
from .models import Hotel, HotelBooking, HotelImage, HotelMember, HotelReview, RoomType


class RoomTypeInline(ReadOnlyInline):
    model = RoomType
    fields = ["name", "capacity", "beds", "price_per_night_uzs", "total_rooms", "image", "is_active"]


class HotelImageInline(ReadOnlyInline):
    model = HotelImage
    fields = ["kind", "image", "caption", "is_cover"]


class HotelMemberInline(ReadOnlyInline):
    model = HotelMember
    fields = ["user", "role"]


@admin.register(Hotel)
class HotelAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Mehmonxona ma'lumotlarini faqat egasi o'zgartiradi. Admin — tasdiqlaydi yoki izoh bilan qaytaradi."""

    admin_editable_fields = ("commission_percent", "is_featured")
    list_display = [
        "name",
        "destination",
        "kind",
        "stars",
        "status",
        "commission_percent",
        "rating",
        "is_featured",
    ]
    list_filter = ["status", "kind", "stars", "destination"]
    list_editable = ["commission_percent", "is_featured"]
    search_fields = ["name", "address", "phone"]
    inlines = [RoomTypeInline, HotelImageInline, HotelMemberInline]
    actions = ["approve", "return_to_owner", "suspend"]

    @admin.action(description="✅ Tasdiqlash (saytga chiqadi)")
    def approve(self, request, queryset):
        for h in queryset:
            services.approve_hotel(h)
        self.message_user(request, f"{queryset.count()} ta mehmonxona tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="↩️ Qaytarish (kamchiliklarni yozib)")
    def return_to_owner(self, request, queryset):
        return return_with_note(
            self, request, queryset, apply=services.reject_hotel, title="Mehmonxonani qaytarish"
        )

    @admin.action(description="⛔ To'xtatish")
    def suspend(self, request, queryset):
        n = 0
        for h in queryset:
            h.status = Hotel.Status.SUSPENDED
            h.save(update_fields=["status", "updated_at"])
            user_events.hotel_status(h)
            n += 1
        self.message_user(request, f"{n} ta mehmonxona to'xtatildi.", messages.WARNING)


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ["code", "hotel", "room_type", "check_in", "check_out", "rooms", "total_uzs", "status"]
    list_filter = ["status", "hotel"]
    search_fields = ["code", "contact_name", "contact_phone", "user__email"]
    date_hierarchy = "check_in"
    readonly_fields = [f.name for f in HotelBooking._meta.fields]
    actions = ["mark_paid", "cancel_by_admin"]

    def has_add_permission(self, request):
        return False

    def _run(self, request, queryset, fn, ok):
        done = 0
        for b in queryset:
            try:
                fn(b)
                done += 1
            except ValidationError as exc:
                self.message_user(request, f"{b.code}: {exc.detail}", messages.WARNING)
        if done:
            self.message_user(request, f"{done} ta: {ok}", messages.SUCCESS)

    @admin.action(description="To'langan deb belgilash")
    def mark_paid(self, request, queryset):
        self._run(request, queryset, services.mark_paid, "tasdiqlandi")

    @admin.action(description="Bekor qilish (mehmonga 100%)")
    def cancel_by_admin(self, request, queryset):
        self._run(
            request,
            queryset,
            lambda b: services.cancel(b, by=HotelBooking.CancelledBy.ADMIN, reason="Admin"),
            "bekor qilindi",
        )


@admin.register(HotelReview)
class HotelReviewAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Sharhlar admin tasdiqlagach saytga chiqadi (matnni admin o'zgartirmaydi)."""

    list_display = ["hotel", "user", "rating", "is_published", "created_at"]
    list_filter = ["is_published", "rating"]
    actions = ["publish", "hide"]

    @admin.action(description="✅ E'lon qilish")
    def publish(self, request, queryset):
        for r in queryset:
            services.set_review_published(r, True)
        self.message_user(request, f"{queryset.count()} ta sharh e'lon qilindi.", messages.SUCCESS)

    @admin.action(description="🚫 Yashirish")
    def hide(self, request, queryset):
        for r in queryset:
            services.set_review_published(r, False)
        self.message_user(request, f"{queryset.count()} ta sharh yashirildi.")
