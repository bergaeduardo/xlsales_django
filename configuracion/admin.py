from django.contrib import admin

from .models import ConfiguracionSistema


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ("clave", "valor_truncado", "tipo", "grupo", "editable")
    list_filter = ("tipo", "grupo", "editable")
    search_fields = ("clave", "descripcion")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("grupo", "clave")

    def valor_truncado(self, obj):
        return obj.valor[:60]
    valor_truncado.short_description = "valor"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
