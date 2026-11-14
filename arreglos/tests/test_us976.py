"""Tests US #976 — Detalle de Artículos A2."""
import pytest
from django.contrib.auth.models import Group, User

from arreglos.serializers import DetalleArticuloArregloCreateSerializer, DetalleArticuloArregloSerializer
from arreglos.views import _puede_crear, _puede_editar, _tiene_acceso_lectura


def _make_user(username, groups=()):
    user, _ = User.objects.get_or_create(username=username)
    for g in groups:
        group, _ = Group.objects.get_or_create(name=g)
        user.groups.add(group)
    return user


# ---------------------------------------------------------------------------
# Serializer — CreateSerializer
# ---------------------------------------------------------------------------

def test_create_serializer_cantidad_valida():
    s = DetalleArticuloArregloCreateSerializer(data={"codigo_articulo": "ART001", "cantidad": 2})
    assert s.is_valid(), s.errors
    assert s.validated_data["cantidad"] == 2


def test_create_serializer_cantidad_cero_invalida():
    s = DetalleArticuloArregloCreateSerializer(data={"codigo_articulo": "ART001", "cantidad": 0})
    assert not s.is_valid()
    assert "cantidad" in s.errors


def test_create_serializer_cantidad_negativa_invalida():
    s = DetalleArticuloArregloCreateSerializer(data={"codigo_articulo": "ART001", "cantidad": -1})
    assert not s.is_valid()
    assert "cantidad" in s.errors


def test_create_serializer_sin_codigo_es_valido():
    s = DetalleArticuloArregloCreateSerializer(data={"cantidad": 1})
    assert s.is_valid(), s.errors


def test_create_serializer_con_observacion():
    s = DetalleArticuloArregloCreateSerializer(
        data={"codigo_articulo": "BOLSO-X", "cantidad": 3, "observacion": "Verificar color"}
    )
    assert s.is_valid(), s.errors
    assert s.validated_data["observacion"] == "Verificar color"


# ---------------------------------------------------------------------------
# Permisos de módulo
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_consultor_tiene_acceso_lectura():
    user = _make_user("consultor_test", ["arreglos_consultor"])
    assert _tiene_acceso_lectura(user)


@pytest.mark.django_db
def test_emisor_puede_crear():
    user = _make_user("emisor_test", ["arreglos_emisor"])
    assert _puede_crear(user)


@pytest.mark.django_db
def test_consultor_no_puede_editar():
    user = _make_user("consultor2", ["arreglos_consultor"])
    assert not _puede_editar(user)


@pytest.mark.django_db
def test_admin_puede_editar():
    user = _make_user("admin_test", ["arreglos_admin"])
    assert _puede_editar(user)


@pytest.mark.django_db
def test_sin_grupos_no_tiene_acceso():
    user = _make_user("sin_grupos")
    assert not _tiene_acceso_lectura(user)


# ---------------------------------------------------------------------------
# Serializer — ArregloSerializer (lectura)
# ---------------------------------------------------------------------------

def test_detalle_serializer_campos():
    fields = set(DetalleArticuloArregloSerializer().fields.keys())
    assert "id_detalle_articulo" in fields
    assert "pedido_id" in fields
    assert "codigo_articulo" in fields
    assert "cantidad" in fields
    assert "observacion" in fields
