from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "full_name", "role", "language", "is_active", "date_joined"]
    list_filter = ["role", "language", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    readonly_fields = ["telegram_id", "google_sub"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Shaxsiy", {"fields": ("first_name", "last_name", "phone", "country", "language", "avatar")}),
        ("Tashqi akkauntlar", {"fields": ("telegram_id", "google_sub")}),
        (
            "Rol va ruxsatlar",
            {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Sanalar", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),)
