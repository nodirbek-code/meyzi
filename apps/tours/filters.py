import django_filters
from django.db.models import F
from django.utils import timezone

from apps.guides.models import GuideProfile
from apps.hotels.models import Hotel

from .models import CancellationPolicy, Departure, Tour


class TourFilter(django_filters.FilterSet):
    """TripHub'dagi filtrlar: joylashuv, toifa, narx, kunlar, sana (+ agentlik, siyosat)."""

    destination = django_filters.CharFilter(field_name="destination__slug")
    category = django_filters.CharFilter(
        method="filter_category", help_text="Toifa slug'i, vergul bilan bir nechta"
    )
    agency = django_filters.CharFilter(field_name="agency__slug")
    guide = django_filters.CharFilter(
        method="filter_guide", help_text="Gid slug'i — shu gid olib boradigan turlar"
    )
    hotel = django_filters.CharFilter(
        method="filter_hotel", help_text="Mehmonxona slug'i — shu yerda tunaladigan turlar"
    )
    language = django_filters.CharFilter(
        method="filter_language",
        help_text="Til kodi (uz, ru, en, ja...) — shu tilda gapiradigan gidi bor turlar",
    )
    min_price = django_filters.NumberFilter(field_name="price_uzs", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price_uzs", lookup_expr="lte")
    min_days = django_filters.NumberFilter(field_name="duration_days", lookup_expr="gte")
    max_days = django_filters.NumberFilter(field_name="duration_days", lookup_expr="lte")
    date = django_filters.DateFilter(method="filter_date", help_text="Shu kuni bo'sh joyli jo'nash bor")
    date_from = django_filters.DateFilter(method="filter_date_from")
    date_to = django_filters.DateFilter(method="filter_date_to")
    cancellation_policy = django_filters.ChoiceFilter(choices=CancellationPolicy.choices)

    class Meta:
        model = Tour
        fields = ["is_featured"]

    def filter_category(self, qs, name, value):
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        return qs.filter(categories__slug__in=slugs).distinct() if slugs else qs

    def filter_guide(self, qs, name, value):
        return qs.filter(guides__slug=value, guides__status=GuideProfile.Status.APPROVED).distinct()

    def filter_hotel(self, qs, name, value):
        return qs.filter(hotels__slug=value, hotels__status=Hotel.Status.APPROVED).distinct()

    def filter_language(self, qs, name, value):
        code = value.strip().lower()
        if not code.isalpha():
            return qs.none()
        # JSON ro'yxat matn sifatida: ["uz", "ja"] — Postgres va SQLite'da bir xil ishlaydi
        return qs.filter(
            guides__status=GuideProfile.Status.APPROVED, guides__languages__icontains=f'"{code}"'
        ).distinct()

    def filter_date(self, qs, name, value):
        return qs  # filter_queryset ichida birga qo'llanadi

    filter_date_from = filter_date_to = filter_date

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        data = self.form.cleaned_data
        lookup = {}
        if data.get("date"):
            lookup["date"] = data["date"]
        if data.get("date_from"):
            lookup["date__gte"] = data["date_from"]
        if data.get("date_to"):
            lookup["date__lte"] = data["date_to"]
        if not lookup:
            return qs
        # Bitta jo'nash sanasi barcha shartlarga mos kelishi kerak
        ids = (
            Departure.objects.filter(
                status=Departure.Status.OPEN, seats_booked__lt=F("seats_total"), **lookup
            )
            .filter(date__gte=timezone.localdate())
            .values("tour_id")
        )
        return qs.filter(id__in=ids)
