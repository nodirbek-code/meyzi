from django.contrib import admin, messages
from django.utils.html import format_html
from rest_framework.exceptions import ValidationError

from apps.core.admin_moderation import PartnerDataReadOnlyMixin, log_action, return_with_note

from . import services
from .models import GuideBooking, GuideMeetingPoint, GuideProfile, GuideReview, GuideUnavailableDate


@admin.register(GuideProfile)
class GuideProfileAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Gid ma'lumotlarini faqat gidning o'zi o'zgartiradi. Admin — tasdiqlaydi yoki izoh bilan qaytaradi.

    Admin o'zgartira oladigani — platforma qarorlari: komissiya va "sertifikat tasdiqlangan".
    """

    admin_editable_fields = ("commission_percent", "is_certified")
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
    readonly_fields = ["photo_preview", "certificate_link"]
    actions = ["approve", "return_to_guide", "suspend"]

    @admin.display(description="Rasm")
    def photo_preview(self, obj):
        if not obj.photo:
            return "—"
        return format_html('<img src="{}" style="max-height:160px;border-radius:8px">', obj.photo.url)

    @admin.display(description="Sertifikatni ochish")
    def certificate_link(self, obj):
        if not obj.certificate_file:
            return "—"
        return format_html('<a href="{}" target="_blank">yuklab olish</a>', obj.certificate_file.url)

    @admin.action(description="✅ Tasdiqlash (saytga chiqadi)")
    def approve(self, request, queryset):
        for p in queryset:
            services.approve_profile(p)
            log_action(self, request, p, "✅ Tasdiqlandi")
        self.message_user(request, f"{queryset.count()} ta gid tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="↩️ Qaytarish (kamchiliklarni yozib)")
    def return_to_guide(self, request, queryset):
        return return_with_note(
            self, request, queryset, apply=services.reject_profile, title="Gid profilini qaytarish"
        )

    @admin.action(description="⛔ To'xtatish")
    def suspend(self, request, queryset):
        for p in queryset:
            services.suspend_profile(p, "Admin to'xtatdi")
            log_action(self, request, p, "⛔ To'xtatildi")
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
class GuideReviewAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Sharhlar admin tasdiqlagach saytga chiqadi (matnni admin o'zgartirmaydi)."""

    list_display = ["guide", "user", "rating", "is_moderated", "is_published", "created_at"]
    list_filter = ["is_moderated", "is_published", "rating"]
    actions = ["publish", "hide"]

    @admin.action(description="✅ E'lon qilish")
    def publish(self, request, queryset):
        for r in queryset:
            services.set_review_published(r, True)
            log_action(self, request, r, "✅ Sharh e'lon qilindi")
        self.message_user(request, f"{queryset.count()} ta sharh e'lon qilindi.", messages.SUCCESS)

    @admin.action(description="🚫 Yashirish")
    def hide(self, request, queryset):
        for r in queryset:
            services.set_review_published(r, False)
            log_action(self, request, r, "🚫 Sharh yashirildi")
        self.message_user(request, f"{queryset.count()} ta sharh yashirildi.")


@admin.register(GuideUnavailableDate)
class GuideUnavailableDateAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    list_display = ["guide", "date", "note"]
    date_hierarchy = "date"


@admin.register(GuideMeetingPoint)
class GuideMeetingPointAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    list_display = ["name", "guide", "destination", "address", "is_active"]
    list_filter = ["is_active", "destination"]
    search_fields = ["name", "address", "guide__display_name"]
