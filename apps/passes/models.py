import uuid

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
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitor_name} - {self.destination.name} ({self.pass_type})"

    def is_valid(self) -> bool:
        from django.utils import timezone

        now = timezone.now()
        if not self.is_active:
            return False
        if not (self.valid_from <= now <= self.valid_to):
            return False
        if self.pass_type == self.PassType.SINGLE and self.is_used:
            return False
        return True

    def consume(self) -> None:
        if self.pass_type == self.PassType.SINGLE:
            self.is_used = True
            self.save(update_fields=["is_used", "updated_at"])

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Access Pass"
        verbose_name_plural = "Access Passes"