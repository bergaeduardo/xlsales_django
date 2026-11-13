from django.db import models

from core.models import TimeStampedModel


class PuntoVenta(TimeStampedModel):
    """Punto de venta / sucursal comercial."""

    codigo = models.CharField("código", max_length=10, unique=True)
    nombre = models.CharField("nombre", max_length=100)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    telefono = models.CharField("teléfono", max_length=50, blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "punto de venta"
        verbose_name_plural = "puntos de venta"
        ordering = ["codigo"]
        constraints = [
            models.UniqueConstraint(fields=["codigo"], name="uq_puntoventa_codigo"),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"
