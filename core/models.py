from django.conf import settings
from django.db import models


def _exclude_cross_db_user_fks(instance, exclude):
    """
    Amplía 'exclude' con todos los FK que apuntan a User.

    Necesario porque full_clean() intenta validar FKs contra la BD del modelo.
    Si el modelo está en SQL Server ('xlsales') y User está en PostgreSQL ('default'),
    la validación falla con "usuario no encontrado". db_constraint=False evita la
    restricción en BD; este helper evita la validación en Python también.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    exclude = list(exclude or [])
    for f in instance._meta.get_fields():
        if (
            hasattr(f, "related_model")
            and f.related_model is User
            and hasattr(f, "column")
            and f.name not in exclude
        ):
            exclude.append(f.name)
    return exclude


class CrossDbUserFkModelMixin:
    """
    Mixin para modelos en SQL Server ('xlsales') que tienen FK a User (PostgreSQL).

    Usar en modelos que NO heredan TimeStampedModel pero que sí tienen FK a User.
    Garantiza que full_clean() no intente cruzar la frontera de BD para validar
    la FK (coherente con db_constraint=False).
    """

    def full_clean(self, exclude=None, validate_unique=True, validate_constraints=True):
        exclude = _exclude_cross_db_user_fks(self, exclude)
        super().full_clean(
            exclude=exclude,
            validate_unique=validate_unique,
            validate_constraints=validate_constraints,
        )


class TimeStampedModel(models.Model):
    """
    Modelo base abstracto con auditoría de creación/modificación.

    created_by / updated_by usan db_constraint=False porque User vive en
    PostgreSQL ('default') mientras los modelos de negocio viven en SQL Server
    ('xlsales'). No hay FK enforzada a nivel BD; la integridad se mantiene en
    el código (patrón CrossDbUserFk).
    """

    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Fecha de modificación", auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="creado por",
        db_constraint=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="modificado por",
        db_constraint=False,
    )

    def full_clean(self, exclude=None, validate_unique=True, validate_constraints=True):
        exclude = _exclude_cross_db_user_fks(self, exclude)
        super().full_clean(
            exclude=exclude,
            validate_unique=validate_unique,
            validate_constraints=validate_constraints,
        )

    class Meta:
        abstract = True
