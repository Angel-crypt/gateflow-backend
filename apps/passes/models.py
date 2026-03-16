# Create your models here.
from django.conf import settings
from django.db import models


class AccessPass(models.Model):
    class PassType(models.TextChoices):
        SINGLE = "single", "Single Use"
        DAY = "day", "Day Pass"

    destination = models.ForeignKey(
        "destinations.Destination",
        on_delete=models.CASCADE,
        related_name="access_passes",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_passes",
    )
    visitor_name = models.CharField(max_length=150)
    plate = models.CharField(max_length=20, blank=True)
    pass_type = models.CharField(
        max_length=20,
        choices=PassType.choices,
        default=PassType.DAY,
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitor_name} - {self.destination.name}"