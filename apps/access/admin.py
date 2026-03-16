from django.contrib import admin

from .models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("visitor_name", "destination", "guard", "status", "entry_time", "exit_time")
    list_filter = ("status", "access_type", "destination")
    search_fields = ("visitor_name", "plate", "notes")
