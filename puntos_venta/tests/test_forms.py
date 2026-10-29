"""Tests US #956 — PuntoVentaForm."""
import pytest

from puntos_venta.forms import PuntoVentaForm
from puntos_venta.models import PuntoVenta


def _form(data, instance=None):
    return PuntoVentaForm(data=data, instance=instance)


def _valid_data(**overrides):
    return {"codigo": "VTA001", "nombre": "Venta Central", "activo": True, **overrides}


@pytest.mark.django_db
def test_form_valid_datos_minimos():
    form = _form({"codigo": "VTA001", "nombre": "Venta Central", "activo": True})
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_clean_codigo_upper():
    form = _form(_valid_data(codigo="vta001"))
    assert form.is_valid(), form.errors
    assert form.cleaned_data["codigo"] == "VTA001"


@pytest.mark.django_db
def test_clean_codigo_strip_whitespace():
    form = _form(_valid_data(codigo="  VTA001  "))
    assert form.is_valid(), form.errors
    assert form.cleaned_data["codigo"] == "VTA001"


@pytest.mark.django_db
def test_codigo_duplicado_case_insensitive():
    PuntoVenta.objects.create(codigo="VTA001", nombre="Venta Central")
    form = _form(_valid_data(codigo="vta001", nombre="Otra"))
    assert not form.is_valid()
    assert "codigo" in form.errors


@pytest.mark.django_db
def test_codigo_duplicado_excluye_pk_en_update():
    pv = PuntoVenta.objects.create(codigo="VTA001", nombre="Venta Central")
    form = _form(_valid_data(codigo="vta001", nombre="Venta Central"), instance=pv)
    assert form.is_valid(), form.errors
