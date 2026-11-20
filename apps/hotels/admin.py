from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from . import services
from .models import Hotel, HotelBooking, HotelImage, HotelMember, HotelReview, RoomType


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    fields = ["name", "capacity", "price_per_night_uzs", "total_rooms", "is_active"]


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 0


class HotelMemberInline(admin.TabularInline):
    model = HotelMember
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
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
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["destination"]
    readonly_fields = ["rating", "reviews_count"]
    inlines = [RoomTypeInline, HotelImageInline, HotelMemberInline]
    actions = ["approve", "reject", "suspend"]

    @admin.action(description="✅ Tasdiqlash")
    def approve(self, request, queryset):
        for h in queryset:
            services.approve_hotel(h)
        self.message_user(request, f"{queryset.count()} ta mehmonxona tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="❌ Rad etish (sababni «moderator izohi» ga yozing)")
    def reject(self, request, queryset):
        n = queryset.update(status=Hotel.Status.REJECTED)
        self.message_user(request, f"{n} ta ariza rad etildi.")

    @admin.action(description="⛔ To'xtatish")
    def suspend(self, request, queryset):
        n = queryset.update(status=Hotel.Status.SUSPENDED)
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
class HotelReviewAdmin(admin.ModelAdmin):
    list_display = ["hotel", "user", "rating", "is_published", "created_at"]
    list_filter = ["is_published", "rating"]
    readonly_fields = ["booking", "user", "hotel", "rating", "text"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        services.recalculate_rating(obj.hotel_id)
