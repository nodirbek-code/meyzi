from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from apps.notifications import user_events

from . import services
from .models import GuideBooking, GuideMeetingPoint, GuideProfile, GuideReview, GuideUnavailableDate


@admin.register(GuideProfile)
class GuideProfileAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "phone",
        "status",
        "is_certified",
        "price_full_day_uzs",
        "rating",
        "warnings_count",
        "no_show_count",
    ]
    list_filter = ["status", "is_certified", "destinations"]
    search_fields = ["display_name", "phone", "user__email", "certificate_number"]
    autocomplete_fields = ["user"]
    filter_horizontal = ["destinations"]
    readonly_fields = ["rating", "reviews_count", "approved_at", "certificate_link"]

    @admin.display(description="Sertifikatni ochish")
    def certificate_link(self, obj):
        from django.utils.html import format_html

        if not obj.certificate_file:
            return "—"
        return format_html('<a href="{}" target="_blank">yuklab olish</a>', obj.certificate_file.url)

    actions = ["approve", "reject", "suspend"]

    @admin.action(description="✅ Tasdiqlash")
    def approve(self, request, queryset):
        for p in queryset:
            services.approve_profile(p)
        self.message_user(request, f"{queryset.count()} ta gid tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="❌ Rad etish")
    def reject(self, request, queryset):
        n = 0
        for p in queryset:
            p.status = GuideProfile.Status.REJECTED
            p.save(update_fields=["status", "updated_at"])
            user_events.guide_profile_status(p)
            n += 1
        self.message_user(
            request, f"{n} ta ariza rad etildi. Sababni gid sahifasida «moderator izohi» ga yozing."
        )

    @admin.action(description="⛔ To'xtatish")
    def suspend(self, request, queryset):
        for p in queryset:
            services.suspend_profile(p, "Admin to'xtatdi")
        self.message_user(request, f"{queryset.count()} ta gid to'xtatildi.", messages.WARNING)


@admin.register(GuideBooking)
class GuideBookingAdmin(admin.ModelAdmin):
    list_display = ["code", "guide", "start_date", "duration", "group_size", "total_uzs", "status", "no_show"]
    list_filter = ["status", "duration", "no_show"]
    search_fields = ["code", "contact_name", "contact_phone", "guide__display_name", "user__email"]
    date_hierarchy = "start_date"
    readonly_fields = [f.name for f in GuideBooking._meta.fields]
    actions = ["mark_paid", "guide_no_show", "cancel_by_admin"]

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

    @admin.action(description="🚨 Gid kelmadi (turistga 100%, gidga $25)")
    def guide_no_show(self, request, queryset):
        self._run(request, queryset, services.report_guide_no_show, "gid kelmadi deb belgilandi")

    @admin.action(description="Bekor qilish (turistga 100%)")
    def cancel_by_admin(self, request, queryset):
        self._run(
            request,
            queryset,
            lambda b: services.cancel(b, by=GuideBooking.CancelledBy.ADMIN, reason="Admin"),
            "bekor qilindi",
        )


@admin.register(GuideReview)
class GuideReviewAdmin(admin.ModelAdmin):
    list_display = ["guide", "user", "rating", "is_published", "created_at"]
    list_filter = ["is_published", "rating"]
    readonly_fields = ["booking", "user", "guide", "rating", "text"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        services.recalculate_rating(obj.guide_id)


@admin.register(GuideUnavailableDate)
class GuideUnavailableDateAdmin(admin.ModelAdmin):
    list_display = ["guide", "date", "note"]
    date_hierarchy = "date"


@admin.register(GuideMeetingPoint)
class GuideMeetingPointAdmin(admin.ModelAdmin):
    list_display = ["name", "guide", "destination", "address", "is_active"]
    list_filter = ["is_active", "destination"]
    search_fields = ["name", "address", "guide__display_name"]
    autocomplete_fields = ["guide"]
