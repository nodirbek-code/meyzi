from django.contrib import admin, messages

from apps.notifications import user_events

from .models import Departure, ItineraryDay, ItineraryItem, Tour, TourCategory, TourMedia


@admin.register(TourCategory)
class TourCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


class TourMediaInline(admin.TabularInline):
    model = TourMedia
    extra = 0


class DepartureInline(admin.TabularInline):
    model = Departure
    extra = 0
    fields = ["date", "seats_total", "seats_booked", "price_uzs", "status"]
    readonly_fields = ["seats_booked"]


class ItineraryDayInline(admin.StackedInline):
    model = ItineraryDay
    extra = 0
    show_change_link = True


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ["title", "agency", "destination", "price_uzs", "duration_days", "status", "is_featured"]
    list_filter = ["status", "agency", "destination", "categories", "cancellation_policy", "is_featured"]
    list_editable = ["is_featured"]
    search_fields = ["title", "agency__name"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["agency", "destination"]
    filter_horizontal = ["categories", "places"]
    readonly_fields = ["published_at", "rating", "reviews_count"]
    inlines = [TourMediaInline, ItineraryDayInline, DepartureInline]
    actions = ["approve", "reject"]

    @admin.action(description="Tasdiqlash va e'lon qilish")
    def approve(self, request, queryset):
        n = 0
        for tour in queryset.exclude(status=Tour.Status.PUBLISHED):
            tour.publish()
            tour.moderation_note = ""
            tour.save()
            user_events.tour_moderated(tour)
            n += 1
        self.message_user(request, f"{n} ta tur e'lon qilindi.", messages.SUCCESS)

    @admin.action(description="Rad etish (izohni tur sahifasida yozing)")
    def reject(self, request, queryset):
        n = 0
        for tour in queryset.filter(status=Tour.Status.PENDING_REVIEW):
            tour.status = Tour.Status.REJECTED
            tour.save(update_fields=["status", "updated_at"])
            user_events.tour_moderated(tour)
            n += 1
        self.message_user(request, f"{n} ta tur rad etildi.", messages.WARNING)


class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 0


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    list_display = ["tour", "day_number", "title"]
    inlines = [ItineraryItemInline]


@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    list_display = ["tour", "date", "seats_total", "seats_booked", "status"]
    list_filter = ["status", "date"]
    search_fields = ["tour__title"]
    date_hierarchy = "date"
