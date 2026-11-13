from django import forms

from .models import PuntoVenta


class PuntoVentaForm(forms.ModelForm):
    class Meta:
        model = PuntoVenta
        fields = ["codigo", "nombre", "direccion", "telefono", "activo"]
        widgets = {
            "codigo": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: VTA001"}
            ),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip().upper()
        if not codigo:
            raise forms.ValidationError("El código es obligatorio.")
        qs = PuntoVenta.objects.filter(codigo__iexact=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un punto de venta con ese código.")
        return codigo
