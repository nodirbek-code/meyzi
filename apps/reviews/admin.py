from django.contrib import admin, messages

from apps.core.admin_moderation import PartnerDataReadOnlyMixin, log_action

from . import services
from .models import Review


@admin.register(Review)
class ReviewAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Tur sharhlari admin tasdiqlagach saytga chiqadi. Matnni admin o'zgartirmaydi."""

    list_display = ["tour", "agency", "user", "rating", "status", "created_at"]
    list_filter = ["status", "rating", "agency"]
    search_fields = ["text", "tour__title", "user__email", "booking__code"]
    actions = ["publish", "hide"]

    @admin.action(description="✅ E'lon qilish")
    def publish(self, request, queryset):
        for review in queryset:
            services.set_status(review, Review.Status.PUBLISHED)
            log_action(self, request, review, "✅ Sharh e'lon qilindi")
        self.message_user(request, f"{queryset.count()} ta sharh e'lon qilindi.", messages.SUCCESS)

    @admin.action(description="🚫 Yashirish (reytingdan chiqadi)")
    def hide(self, request, queryset):
        for review in queryset:
            services.set_status(review, Review.Status.HIDDEN, note="Admin yashirdi")
            log_action(self, request, review, "🚫 Sharh yashirildi")
        self.message_user(request, f"{queryset.count()} ta sharh yashirildi.")
