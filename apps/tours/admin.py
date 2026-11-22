from django.contrib import admin, messages

from apps.core.admin_moderation import PartnerDataReadOnlyMixin, ReadOnlyInline, log_action, return_with_note
from apps.notifications import user_events

from .models import Departure, ItineraryDay, ItineraryItem, Tour, TourCategory, TourMedia


@admin.register(TourCategory)
class TourCategoryAdmin(admin.ModelAdmin):
    """Toifalar — platformaning o'z ma'lumoti (admin boshqaradi)."""

    list_display = ["name", "slug", "icon", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


class TourMediaInline(ReadOnlyInline):
    model = TourMedia
    fields = ["kind", "file", "caption", "is_cover"]


class DepartureInline(ReadOnlyInline):
    model = Departure
    fields = ["date", "seats_total", "seats_booked", "price_uzs", "status"]


class ItineraryDayInline(ReadOnlyInline):
    model = ItineraryDay
    fields = ["day_number", "title"]


@admin.register(Tour)
class TourAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Turni faqat agentlik o'zgartiradi. Admin — tasdiqlaydi yoki izoh bilan qaytaradi."""

    admin_editable_fields = ("is_featured",)
    list_display = ["title", "agency", "destination", "price_uzs", "duration_days", "status", "is_featured"]
    list_filter = ["status", "agency", "destination", "categories", "cancellation_policy", "is_featured"]
    list_editable = ["is_featured"]
    search_fields = ["title", "agency__name"]
    inlines = [TourMediaInline, ItineraryDayInline, DepartureInline]
    actions = ["approve", "return_to_agency"]

    @admin.action(description="✅ Tasdiqlash va e'lon qilish")
    def approve(self, request, queryset):
        n = 0
        for tour in queryset.exclude(status=Tour.Status.PUBLISHED):
            tour.publish()
            tour.moderation_note = ""
            tour.save()
            user_events.tour_moderated(tour)
            log_action(self, request, tour, "✅ Tasdiqlandi va e'lon qilindi")
            n += 1
        self.message_user(request, f"{n} ta tur e'lon qilindi.", messages.SUCCESS)

    @admin.action(description="↩️ Qaytarish (kamchiliklarni yozib)")
    def return_to_agency(self, request, queryset):
        from .views import reject_tour

        return return_with_note(
            self,
            request,
            queryset.exclude(status=Tour.Status.DRAFT),
            apply=reject_tour,
            title="Turni agentlikka qaytarish",
        )


class ItineraryItemInline(ReadOnlyInline):
    model = ItineraryItem


@admin.register(ItineraryDay)
class ItineraryDayAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    list_display = ["tour", "day_number", "title"]
    inlines = [ItineraryItemInline]


@admin.register(Departure)
class DepartureAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    list_display = ["tour", "date", "seats_total", "seats_booked", "status"]
    list_filter = ["status", "date"]
    search_fields = ["tour__title"]
    date_hierarchy = "date"
