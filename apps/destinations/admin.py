from django.contrib import admin

from .models import Destination, IndustrialPark


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    model = Destination

    list_display = ["name", "type", "park", "responsible", "is_active"]
    list_filter = ["type", "is_active", "park"]
    search_fields = ["name", "park__name", "responsible__email"]


@admin.register(IndustrialPark)
class IndustrialParkAdmin(admin.ModelAdmin):
    list_display = ["name", "address", "created_at", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "address"]
