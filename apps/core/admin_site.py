"""MEYZI admin sayti: bosh sahifa — dashboard (tekshiruv navbati, pul, ogohlantirishlar, platforma holati).

`INSTALLED_APPS` da "django.contrib.admin" o'rniga `apps.core.admin_site.MeyziAdminConfig`.
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig


class MeyziAdminSite(admin.AdminSite):
    site_header = f"{settings.BRAND_NAME} — boshqaruv paneli"
    site_title = f"{settings.BRAND_NAME} admin"
    index_title = "Dashboard"
    index_template = "admin/meyzi_dashboard.html"

    def has_permission(self, request):
        """Django admin — faqat asosiy admin (soha moderatorlari faqat /control da ishlaydi)."""
        user = request.user
        return bool(
            user.is_active and user.is_staff and (user.is_superuser or not getattr(user, "staff_area", ""))
        )

    def index(self, request, extra_context=None):
        from . import dashboard

        return super().index(request, {**dashboard.context(), **(extra_context or {})})


class MeyziAdminConfig(AdminConfig):
    default_site = "apps.core.admin_site.MeyziAdminSite"
