from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from . import services
from .models import Agency, AgencyApplication, AgencyMember


class AgencyMemberInline(admin.TabularInline):
    model = AgencyMember
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "status",
        "is_verified",
        "is_platform",
        "auto_publish",
        "commission_percent",
        "rating",
    ]
    list_filter = ["status", "is_verified", "is_platform"]
    list_editable = ["status", "is_verified", "auto_publish", "commission_percent"]
    search_fields = ["name", "phone", "inn"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AgencyMemberInline]


@admin.register(AgencyApplication)
class AgencyApplicationAdmin(admin.ModelAdmin):
    list_display = ["agency_name", "contact_person", "phone", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["agency_name", "contact_person", "phone"]
    readonly_fields = ["user", "reviewed_by", "reviewed_at", "agency"]
    actions = ["approve", "reject"]

    @admin.action(description="Tasdiqlash (agentlik yaratiladi)")
    def approve(self, request, queryset):
        self._run(request, queryset, lambda a: services.approve_application(a, request.user))

    @admin.action(description="Rad etish")
    def reject(self, request, queryset):
        self._run(request, queryset, lambda a: services.reject_application(a, request.user))

    def _run(self, request, queryset, fn):
        done = 0
        for application in queryset:
            try:
                fn(application)
                done += 1
            except ValidationError as exc:
                self.message_user(request, f"{application}: {exc.detail}", messages.WARNING)
        if done:
            self.message_user(request, f"{done} ta ariza qayta ishlandi.", messages.SUCCESS)
