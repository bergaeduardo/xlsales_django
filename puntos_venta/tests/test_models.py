"""Tests US #956 — PuntoVenta model."""
import pytest
from django.db import IntegrityError

from puntos_venta.models import PuntoVenta


def _make(codigo="VTA001", nombre="Venta Central", **kwargs):
    return PuntoVenta.objects.create(codigo=codigo, nombre=nombre, **kwargs)


@pytest.mark.django_db
def test_crear_valido_activo_default():
    pv = _make()
    assert pv.pk is not None
    assert pv.activo is True


@pytest.mark.django_db
def test_codigo_unique():
    _make(codigo="VTA001")
    with pytest.raises(IntegrityError):
        _make(codigo="VTA001", nombre="Otro")


@pytest.mark.django_db
def test_str_incluye_codigo_y_nombre():
    pv = _make(codigo="VTA002", nombre="Sucursal Norte")
    assert "VTA002" in str(pv)
    assert "Sucursal Norte" in str(pv)


@pytest.mark.django_db
def test_ordering_por_codigo():
    _make(codigo="ZZZ", nombre="Z")
    _make(codigo="AAA", nombre="A")
    _make(codigo="MMM", nombre="M")
    codigos = list(PuntoVenta.objects.values_list("codigo", flat=True))
    assert codigos == sorted(codigos)


@pytest.mark.django_db
def test_soft_delete_marker():
    pv = _make()
    pv.activo = False
    pv.save(update_fields=["activo"])
    pv.refresh_from_db()
    assert pv.activo is False
    assert PuntoVenta.objects.filter(pk=pv.pk).exists()


@pytest.mark.django_db
def test_timestamps_auto():
    pv = _make()
    assert pv.created_at is not None
    assert pv.updated_at is not None
