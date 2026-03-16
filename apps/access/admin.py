from django.contrib import admin

from .models import AccessLog, AccessPass


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("visitor_name", "destination", "guard", "status", "entry_time", "exit_time")
    list_filter = ("status", "access_type", "destination")
    search_fields = ("visitor_name", "plate", "notes")


@admin.register(AccessPass)
class AccessPassAdmin(admin.ModelAdmin):
    list_display = ("visitor_name", "destination", "created_by", "pass_type", "valid_from", "valid_to", "is_active")
    list_filter = ("pass_type", "is_active", "destination")
    search_fields = ("visitor_name", "plate")