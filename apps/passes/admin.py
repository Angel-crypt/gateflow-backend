# Register your models here.
from django.contrib import admin

from .models import AccessPass


@admin.register(AccessPass)
class AccessPassAdmin(admin.ModelAdmin):
    list_display = (
        "visitor_name",
        "destination",
        "created_by",
        "pass_type",
        "valid_from",
        "valid_to",
        "is_active",
    )
    list_filter = ("pass_type", "is_active", "destination")
    search_fields = ("visitor_name", "plate")
