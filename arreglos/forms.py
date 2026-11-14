"""Formularios para el módulo de Pedidos de Reparación."""
from django import forms

from .models import PedidoArreglo


class PedidoArregloForm(forms.ModelForm):
    class Meta:
        model = PedidoArreglo
        fields = [
            "cliente", "email", "telefono",
            "fecha_solicitud", "fecha_de_compra",
            "articulo", "descripcion", "observaciones", "recibido",
            "bolsin", "bolsin_egreso",
            "forro", "cierre", "costura", "correa", "herraje", "otro",
            "txt_forro", "txt_cierre", "txt_costura", "txt_correa", "txt_herraje", "txt_otro",
            "id_comprobante",
        ]
        widgets = {
            "fecha_solicitud": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "fecha_de_compra": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }
