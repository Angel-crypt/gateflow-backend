from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.destinations.models import Destination, IndustrialPark


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        GUARD = "guard", "Guardia"
        COMPANY = "company", "Empresa"

    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    park = models.ForeignKey(
        IndustrialPark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    destinations = models.ManyToManyField(
        Destination,
        blank=True,
        related_name="company_users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    objects = UserManager()  # type: ignore[misc,assignment]

    def __str__(self):
        return f"{self.email} ({self.role})"
