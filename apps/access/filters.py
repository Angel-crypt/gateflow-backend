import django_filters

from .models import AccessLog


class AccessLogFilter(django_filters.FilterSet):
    date_from = django_filters.DateTimeFilter(field_name="entry_time", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="entry_time", lookup_expr="lte")
    destination = django_filters.NumberFilter(field_name="destination__id")

    class Meta:
        model = AccessLog
        fields = ["access_type", "status", "destination", "date_from", "date_to"]
