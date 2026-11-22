from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.admin_views import private_file
from apps.core.views import FeaturesView, HealthView

api_v1 = [
    path("features/", FeaturesView.as_view(), name="features"),
    path("auth/", include("apps.accounts.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("agencies/", include("apps.agencies.urls")),
    path("tours/", include("apps.tours.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("payments/", include("apps.payments.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("guides/", include("apps.guides.urls")),
    path("guide-bookings/", include("apps.guides.booking_urls")),
    path("hotels/", include("apps.hotels.urls")),
    path("hotel-bookings/", include("apps.hotels.booking_urls")),
    path("", include("apps.content.urls")),
    path("cabinet/", include("apps.tours.cabinet_urls")),
    path("control/", include("apps.core.control_urls")),  # saytdagi admin paneli (/control)
]

urlpatterns = [
    # Django admin — /control/admin/ (oddiy /admin/ manzili yo'q)
    path("control/admin/private/<path:path>", private_file, name="private-file"),
    path("control/admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "SERVE_MEDIA", False):
    # nginx'siz hosting (Render): media fayllarni Django o'zi beradi
    from django.urls import re_path
    from django.views.static import serve

    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
