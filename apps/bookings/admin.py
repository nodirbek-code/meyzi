from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from . import services
from .models import Booking, Traveler


class TravelerInline(admin.TabularInline):
    model = Traveler
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["code", "tour", "departure_at", "user", "seats", "total_uzs", "status", "created_at"]
    list_filter = ["status", "agency", "cancellation_policy"]
    search_fields = ["code", "contact_name", "contact_phone", "user__email", "tour__title"]
    date_hierarchy = "departure_at"
    inlines = [TravelerInline]
    readonly_fields = [f.name for f in Booking._meta.fields]
    actions = ["mark_paid", "cancel_by_admin"]

    def has_add_permission(self, request):
        return False  # bron faqat API orqali (joylar soni to'g'ri hisoblanishi uchun)

    @admin.action(description="To'langan deb belgilash (tasdiqlash)")
    def mark_paid(self, request, queryset):
        self._run(request, queryset, services.confirm_booking)

    @admin.action(description="Bekor qilish (turistga 100% qaytariladi)")
    def cancel_by_admin(self, request, queryset):
        self._run(
            request,
            queryset,
            lambda b: services.cancel_booking(b, by=Booking.CancelledBy.ADMIN, reason="Admin"),
        )

    def _run(self, request, queryset, fn):
        done = 0
        for booking in queryset:
            try:
                fn(booking)
                done += 1
            except ValidationError as exc:
                self.message_user(request, f"{booking.code}: {exc.detail}", messages.WARNING)
        if done:
            self.message_user(request, f"{done} ta bron qayta ishlandi.", messages.SUCCESS)
