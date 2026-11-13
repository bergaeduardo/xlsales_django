import json
from decimal import Decimal, InvalidOperation

from django import forms

from .models import ConfiguracionSistema, TipoDato


class ConfiguracionSistemaCreateForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSistema
        fields = ["clave", "valor", "tipo", "descripcion", "grupo", "editable"]
        widgets = {
            "clave": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej. app.version"}),
            "valor": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "grupo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej. integracion.tango"}),
            "editable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ConfiguracionSistemaUpdateForm(forms.ModelForm):
    """Permite editar valor, descripcion, grupo y editable. Clave y tipo son inmutables."""

    class Meta:
        model = ConfiguracionSistema
        fields = ["valor", "descripcion", "grupo", "editable"]
        widgets = {
            "valor": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "grupo": forms.TextInput(attrs={"class": "form-control"}),
            "editable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor", "")
        tipo = self.instance.tipo
        try:
            if tipo == TipoDato.INT:
                int(valor)
            elif tipo == TipoDato.BOOL:
                if valor.lower() not in {"true", "false", "1", "0"}:
                    raise ValueError
            elif tipo == TipoDato.JSON:
                json.loads(valor)
            elif tipo == TipoDato.DECIMAL:
                Decimal(valor)
        except (ValueError, TypeError, json.JSONDecodeError, InvalidOperation):
            raise forms.ValidationError(
                f"El valor no es válido para el tipo «{self.instance.get_tipo_display()}»."
            )
        return valor
