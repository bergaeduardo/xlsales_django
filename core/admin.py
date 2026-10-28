from django.contrib.auth import get_user_model


class CrossDbUserFkAdminMixin:
    """
    Mixin para ModelAdmin de modelos en SQL Server ('xlsales') con FK a User.

    PROBLEMA: el admin genera el queryset del FK a User usando la BD del modelo
    padre → 'xlsales'. Como auth_user no existe en SQL Server, el dropdown queda
    vacío y al guardar falla.

    SOLUCIÓN: interceptar formfield_for_foreignkey y forzar using('default')
    para cualquier FK que apunte a User.

    Usar junto con CrossDbUserFkModelMixin en el modelo correspondiente.
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        User = get_user_model()
        if db_field.related_model is User:
            kwargs["queryset"] = User.objects.using("default").all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
