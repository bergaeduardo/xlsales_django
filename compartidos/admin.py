from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PerfilUsuario
from .roles import sync_grupos

User = get_user_model()

_NINGUNO = ""
_ARREGLOS_CHOICES = [
    (_NINGUNO, "— ninguno —"),
    ("arreglos_admin", "Administrador"),
    ("arreglos_operador", "Operador"),
    ("arreglos_consultor", "Consultor"),
    ("arreglos_deposito", "Depósito"),
    ("arreglos_emisor", "Emisor"),
    ("arreglos_fabrica", "Fábrica"),
]
_CADS_CHOICES = [
    (_NINGUNO, "— ninguno —"),
    ("cads_admin", "Administrador"),
    ("cads_operador", "Operador"),
    ("cads_contabilidad", "Contabilidad"),
    ("cads_deposito", "Depósito"),
    ("cads_emisor", "Emisor"),
    ("cads_emisor_mayorista", "Emisor Mayorista"),
    ("cads_responsable_comercial", "Responsable Comercial"),
]


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    fk_name = "user"
    can_delete = False
    verbose_name = "Perfil legacy"
    fields = ("usuario_legacy_id",)
    extra = 0


class UserRolForm(forms.ModelForm):
    rol_arreglos = forms.ChoiceField(
        choices=_ARREGLOS_CHOICES,
        required=False,
        label="Rol Arreglos",
    )
    rol_cads = forms.ChoiceField(
        choices=_CADS_CHOICES,
        required=False,
        label="Rol CADS",
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            grupos = set(self.instance.groups.values_list("name", flat=True))
            for nombre, _ in _ARREGLOS_CHOICES[1:]:
                if nombre in grupos:
                    self.initial["rol_arreglos"] = nombre
                    break
            for nombre, _ in _CADS_CHOICES[1:]:
                if nombre in grupos:
                    self.initial["rol_cads"] = nombre
                    break


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserRolForm
    inlines = [PerfilUsuarioInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Roles XLSales", {"fields": ("rol_arreglos", "rol_cads")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Roles XLSales", {"fields": ("rol_arreglos", "rol_cads")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cd = form.cleaned_data
        sync_grupos(
            obj,
            cd.get("rol_arreglos") or None,
            cd.get("rol_cads") or None,
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "usuario_legacy_id", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "usuario_legacy_id")
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
