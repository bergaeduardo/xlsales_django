import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class TipoDato(models.TextChoices):
    STRING = "string", "Texto"
    INT = "int", "Entero"
    BOOL = "bool", "Booleano"
    JSON = "json", "JSON"
    DECIMAL = "decimal", "Decimal"


class ConfiguracionSistema(TimeStampedModel):
    clave = models.CharField("clave", max_length=100, unique=True, db_index=True)
    valor = models.TextField("valor")
    tipo = models.CharField("tipo de dato", max_length=20, choices=TipoDato.choices, default=TipoDato.STRING)
    descripcion = models.CharField("descripción", max_length=255, blank=True)
    grupo = models.CharField("grupo", max_length=50, blank=True, db_index=True)
    editable = models.BooleanField("editable", default=True)

    class Meta:
        verbose_name = "configuración del sistema"
        verbose_name_plural = "configuraciones del sistema"
        ordering = ["grupo", "clave"]

    def __str__(self):
        return f"{self.clave} = {self.valor[:40]}"

    def clean(self):
        super().clean()
        if self.tipo == TipoDato.INT:
            try:
                int(self.valor)
            except (ValueError, TypeError):
                raise ValidationError({"valor": f"El valor '{self.valor}' no es un entero válido."})
        elif self.tipo == TipoDato.BOOL:
            if (self.valor or "").lower() not in {"true", "false", "1", "0"}:
                raise ValidationError({"valor": f"El valor '{self.valor}' no es un booleano válido (use true/false/1/0)."})
        elif self.tipo == TipoDato.JSON:
            try:
                json.loads(self.valor)
            except (json.JSONDecodeError, TypeError):
                raise ValidationError({"valor": f"El valor no es JSON válido."})
        elif self.tipo == TipoDato.DECIMAL:
            try:
                Decimal(self.valor)
            except (InvalidOperation, TypeError):
                raise ValidationError({"valor": f"El valor '{self.valor}' no es un decimal válido."})
