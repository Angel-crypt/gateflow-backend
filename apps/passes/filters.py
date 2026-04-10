import django_filters

from .models import AccessPass


class AccessPassFilter(django_filters.FilterSet):
    date_from = django_filters.DateTimeFilter(field_name="valid_from", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="valid_to", lookup_expr="lte")
    destination = django_filters.NumberFilter(field_name="destination__id")

    class Meta:
        model = AccessPass
        fields = ["pass_type", "is_active", "destination", "date_from", "date_to"]
