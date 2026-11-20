from django.contrib import admin

from .models import Article, FaqItem, Page


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "destination", "status", "published_at"]
    list_filter = ["status", "destination"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["destination"]
    filter_horizontal = ["tours"]
    readonly_fields = ["published_at"]

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(FaqItem)
class FaqItemAdmin(admin.ModelAdmin):
    list_display = ["question", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "is_published", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
