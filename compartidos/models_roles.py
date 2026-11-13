from django.db import models


class RolArreglos(models.Model):
    """
    Tabla legacy ar_UsuariosRoles en SQL Server (xlsales). Solo lectura.
    Contiene los roles disponibles para el módulo Arreglos.
    """

    id = models.UUIDField(primary_key=True, db_column="id")
    rol = models.CharField(max_length=50, db_column="rol")

    class Meta:
        managed = False
        db_table = "ar_UsuariosRoles"
        app_label = "compartidos"
        verbose_name = "Rol Arreglos"
        verbose_name_plural = "Roles Arreglos"

    def __str__(self):
        return self.rol


class RolCads(models.Model):
    """
    Tabla legacy Rol_Cads en SQL Server (xlsales). Solo lectura.
    Contiene los roles disponibles para el módulo CADS.
    """

    id_rol_cads = models.UUIDField(primary_key=True, db_column="IdRol_Cads")
    descripcion = models.CharField(max_length=50, blank=True, null=True, db_column="Descripcion")
    activo = models.BooleanField(db_column="Activo")

    class Meta:
        managed = False
        db_table = "Rol_Cads"
        app_label = "compartidos"
        verbose_name = "Rol CADS"
        verbose_name_plural = "Roles CADS"

    def __str__(self):
        return self.descripcion or str(self.id_rol_cads)
