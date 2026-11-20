from django.contrib import admin

from .models import Destination, Place, PlaceImage


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ["name", "region", "is_featured", "is_published", "sort_order"]
    list_editable = ["is_featured", "is_published", "sort_order"]
    search_fields = ["name", "region"]
    prepopulated_fields = {"slug": ("name",)}


class PlaceImageInline(admin.TabularInline):
    model = PlaceImage
    extra = 1


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ["name", "destination", "category", "entry_fee_uzs", "is_featured", "is_published"]
    list_filter = ["destination", "category", "is_featured", "is_published"]
    list_editable = ["is_featured", "is_published"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["destination"]
    inlines = [PlaceImageInline]
