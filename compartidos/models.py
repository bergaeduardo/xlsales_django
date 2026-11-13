from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Usuarios(models.Model):
    """
    Tabla legacy xlsales. Solo lectura. Se incluyen únicamente los campos usados
    por xlsales_django (auth + mapeo de roles). Resto omitido: no afecta DDL
    porque managed=False.
    """

    id = models.UUIDField(primary_key=True, db_column="id")
    alias = models.CharField(max_length=20, db_column="alias")
    nombre = models.CharField(max_length=50, blank=True, null=True, db_column="nombre")
    apellido = models.CharField(max_length=50, blank=True, null=True, db_column="apellido")
    email = models.EmailField(max_length=50, blank=True, null=True, db_column="email")
    activo = models.BooleanField(db_column="activo")
    eliminado = models.BooleanField(db_column="Eliminado")
    id_rol = models.UUIDField(null=True, blank=True, db_column="idRol")
    id_rol_ar = models.UUIDField(null=True, blank=True, db_column="idRol_ar")
    id_rol_cads = models.UUIDField(null=True, blank=True, db_column="idrolcads")
    cod_empleado_tango = models.CharField(
        max_length=50, blank=True, null=True, db_column="CodEmpleadoTango"
    )

    class Meta:
        managed = False
        db_table = "Usuarios"
        app_label = "compartidos"
        verbose_name = "Usuario legacy"
        verbose_name_plural = "Usuarios legacy"

    def __str__(self):
        return f"{self.apellido or ''}, {self.nombre or ''} ({self.alias})"


class PerfilUsuario(TimeStampedModel):
    """
    Perfil Django que vincula auth.User con el usuario legacy de SQL Server.

    Vive en PostgreSQL ('default'). La relación con Usuarios es conceptual:
    usuario_legacy_id almacena el UUID sin FK enforced (cross-DB).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="usuario Django",
    )
    # Referencia al PK de Usuarios en xlsales; sin FK a nivel BD (cross-DB).
    usuario_legacy_id = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="ID usuario legacy",
        help_text="UUID correspondiente a Usuarios.id en SQL Server.",
    )

    class Meta:
        app_label = "compartidos"
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.user}"
