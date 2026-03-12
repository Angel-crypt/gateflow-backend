from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ["email"]

    list_display = ["email", "username", "role", "park", "is_active"]
    list_filter = ["role", "is_active", "park"]
    search_fields = ["email", "username"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("username", "first_name", "last_name")}),
        ("Parque Industrial", {"fields": ("role", "park")}),
        ("Destinos", {"fields": ("destinations",)}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "role", "park", "destinations", "password1", "password2", "is_active"),
            },
        ),
    )
