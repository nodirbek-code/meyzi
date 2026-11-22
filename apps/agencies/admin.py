from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

from apps.core.admin_moderation import PartnerDataReadOnlyMixin, ReadOnlyInline, log_action, return_with_note

from . import services
from .models import Agency, AgencyApplication, AgencyMember


class AgencyMemberInline(ReadOnlyInline):
    model = AgencyMember
    fields = ["user", "role"]


@admin.register(Agency)
class AgencyAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    """Agentlik profilini faqat agentlik o'zgartiradi; o'zgarishlar admin tasdig'idan keyin saytga chiqadi.

    Admin o'zgartira oladigani — platforma qarorlari: komissiya, "tekshirilgan", avto e'lon (faqat platforma).
    """

    admin_editable_fields = ("commission_percent", "is_verified", "auto_publish")
    list_display = [
        "name",
        "moderation_status",
        "status",
        "is_verified",
        "is_platform",
        "commission_percent",
        "rating",
    ]
    list_filter = ["moderation_status", "status", "is_verified", "is_platform"]
    list_editable = ["is_verified", "commission_percent"]
    search_fields = ["name", "phone", "inn"]
    inlines = [AgencyMemberInline]
    actions = ["approve", "return_to_agency", "suspend", "activate"]

    @admin.action(description="✅ Profil o'zgarishlarini tasdiqlash")
    def approve(self, request, queryset):
        for a in queryset:
            services.approve_agency(a)
            log_action(self, request, a, "✅ Profil tasdiqlandi")
        self.message_user(request, f"{queryset.count()} ta agentlik tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="↩️ Qaytarish (kamchiliklarni yozib)")
    def return_to_agency(self, request, queryset):
        return return_with_note(
            self, request, queryset, apply=services.return_agency, title="Agentlik profilini qaytarish"
        )

    @admin.action(description="⛔ To'xtatish (sayt va kabinet yopiladi)")
    def suspend(self, request, queryset):
        n = queryset.update(status=Agency.Status.SUSPENDED)
        self.message_user(request, f"{n} ta agentlik to'xtatildi.", messages.WARNING)

    @admin.action(description="▶️ Faollashtirish")
    def activate(self, request, queryset):
        n = queryset.update(status=Agency.Status.ACTIVE)
        self.message_user(request, f"{n} ta agentlik faollashtirildi.", messages.SUCCESS)


@admin.register(AgencyApplication)
class AgencyApplicationAdmin(PartnerDataReadOnlyMixin, admin.ModelAdmin):
    list_display = ["agency_name", "contact_person", "phone", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["agency_name", "contact_person", "phone"]
    actions = ["approve", "return_application"]

    @admin.action(description="✅ Tasdiqlash (agentlik yaratiladi)")
    def approve(self, request, queryset):
        def approve(application):
            services.approve_application(application, request.user)
            log_action(self, request, application, "✅ Ariza tasdiqlandi, agentlik yaratildi")

        self._run(request, queryset, approve)

    @admin.action(description="↩️ Rad etish (sababini yozib)")
    def return_application(self, request, queryset):
        def apply(application, note):
            try:
                services.reject_application(application, request.user, note)
            except ValidationError as exc:
                self.message_user(request, f"{application}: {exc.detail}", messages.WARNING)

        return return_with_note(self, request, queryset, apply=apply, title="Agentlik arizasini rad etish")

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
