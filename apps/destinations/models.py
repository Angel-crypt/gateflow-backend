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
