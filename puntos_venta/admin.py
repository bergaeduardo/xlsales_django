from django.contrib import admin

from core.admin import CrossDbUserFkAdminMixin

from .models import PuntoVenta


@admin.register(PuntoVenta)
class PuntoVentaAdmin(CrossDbUserFkAdminMixin, admin.ModelAdmin):
    list_display = ("codigo", "nombre", "direccion", "telefono", "activo")
    search_fields = ("codigo", "nombre")
    list_filter = ["activo"]
    ordering = ["codigo"]
