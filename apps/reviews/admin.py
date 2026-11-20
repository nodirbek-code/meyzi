from django.contrib import admin

from . import services
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["tour", "agency", "user", "rating", "status", "created_at"]
    list_filter = ["status", "rating", "agency"]
    search_fields = ["text", "tour__title", "user__email", "booking__code"]
    readonly_fields = [
        "booking",
        "user",
        "tour",
        "agency",
        "rating",
        "text",
        "agency_reply",
        "agency_replied_at",
    ]
    actions = ["hide", "publish"]

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        services.recalculate_ratings(tour_id=obj.tour_id, agency_id=obj.agency_id)

    @admin.action(description="Yashirish (reytingdan chiqadi)")
    def hide(self, request, queryset):
        for review in queryset:
            services.set_status(review, Review.Status.HIDDEN, note="Admin yashirdi")
        self.message_user(request, f"{queryset.count()} ta sharh yashirildi.")

    @admin.action(description="E'lon qilish")
    def publish(self, request, queryset):
        for review in queryset:
            services.set_status(review, Review.Status.PUBLISHED)
        self.message_user(request, f"{queryset.count()} ta sharh e'lon qilindi.")
