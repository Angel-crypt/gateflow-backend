from django.conf import settings
from django.db import models


class AccessLog(models.Model):
    class AccessType(models.TextChoices):
        QR = "qr", "QR"
        MANUAL = "manual", "Manual"

    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        CLOSED = "closed", "Cerrado"

    access_pass = models.ForeignKey(
        "passes.AccessPass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
    )
    destination = models.ForeignKey(
        "destinations.Destination",
        on_delete=models.CASCADE,
        related_name="access_logs",
    )
    guard = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_access_logs",
    )
    visitor_name = models.CharField(max_length=150)
    plate = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    access_type = models.CharField(
        max_length=10,
        choices=AccessType.choices,
        default=AccessType.QR,
    )
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitor_name} - {self.destination.name} ({self.status})"

    def register_exit(self):
        from django.utils import timezone

        self.exit_time = timezone.now()
        self.status = self.Status.CLOSED
        self.save(update_fields=["exit_time", "status", "updated_at"])

    class Meta:
        ordering = ["-entry_time"]
        verbose_name = "Access Log"
        verbose_name_plural = "Access Logs"


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
    qr_token = models.CharField(max_length=255, unique=True)
    pass_type = models.CharField(
        max_length=20,
        choices=PassType.choices,
        default=PassType.SINGLE,
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.visitor_name} → {self.destination.name}"