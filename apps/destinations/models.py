from django.db import models


class IndustrialPark(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Parque Industrial"
        verbose_name_plural = "Parques Industriales"

    def __str__(self) -> str:
        return self.name


class Destination(models.Model):
    class Type(models.TextChoices):
        COMPANY = "company", "Empresa"
        AREA = "area", "Área"

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=Type.choices)
    contact_info = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    park = models.ForeignKey(
        IndustrialPark,
        on_delete=models.CASCADE,
        related_name="destinations",
    )

    class Meta:
        verbose_name = "Destino"
        verbose_name_plural = "Destinos"

    def __str__(self) -> str:
        return f"{self.name} ({self.park})"
