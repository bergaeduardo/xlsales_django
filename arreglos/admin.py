from django.contrib import admin

from .models import DetalleArticuloArreglo, PedidoArreglo


class DetalleArticuloInline(admin.TabularInline):
    model = DetalleArticuloArreglo
    extra = 0
    fields = ["codigo_articulo", "cantidad", "observacion"]
    can_delete = True


@admin.register(PedidoArreglo)
class PedidoArregloAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "estado", "fecha_solicitud"]
    list_filter = ["estado"]
    search_fields = ["cliente", "email"]
    inlines = [DetalleArticuloInline]
