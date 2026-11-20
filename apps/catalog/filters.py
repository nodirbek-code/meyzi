import django_filters

from .models import Place, PlaceCategory


class PlaceFilter(django_filters.FilterSet):
    destination = django_filters.CharFilter(field_name="destination__slug")
    category = django_filters.MultipleChoiceFilter(choices=PlaceCategory.choices)
    is_free = django_filters.BooleanFilter(method="filter_is_free")
    max_fee = django_filters.NumberFilter(field_name="entry_fee_uzs", lookup_expr="lte")

    class Meta:
        model = Place
        fields = ["destination", "category", "is_featured", "is_free", "max_fee"]

    def filter_is_free(self, queryset, name, value):
        return queryset.filter(entry_fee_uzs=0) if value else queryset.exclude(entry_fee_uzs=0)
