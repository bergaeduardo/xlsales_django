"""Tests US #975 — Pedidos de Reparación, flujo de estados A1."""
import pytest
from django.contrib.auth.models import Group

from arreglos.models import EstadoArreglo
from arreglos.serializers import CambiarEstadoSerializer, PedidoArregloCreateSerializer
from arreglos.views import _get_transiciones_permitidas, _puede_crear, _puede_editar


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_group(user, name):
    group, _ = Group.objects.get_or_create(name=name)
    user.groups.add(group)
    return user


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def test_cambiar_estado_serializer_valido():
    s = CambiarEstadoSerializer(data={"estado": EstadoArreglo.ENVIADO})
    assert s.is_valid(), s.errors
    assert s.validated_data["estado"] == EstadoArreglo.ENVIADO


def test_cambiar_estado_serializer_invalido():
    s = CambiarEstadoSerializer(data={"estado": 99})
    assert not s.is_valid()
    assert "estado" in s.errors


def test_create_serializer_default_estado_borrador():
    import datetime
    data = {
        "cliente": "Test SA",
        "fecha_solicitud": "2026-01-01T10:00:00",
        "fecha_de_compra": "2025-12-01T10:00:00",
        "id_comprobante": 1001,
    }
    s = PedidoArregloCreateSerializer(data=data)
    assert s.is_valid(), s.errors
    assert s.validated_data["estado"] == EstadoArreglo.BORRADOR


def test_create_serializer_id_comprobante_invalido():
    data = {
        "cliente": "Test SA",
        "fecha_solicitud": "2026-01-01T10:00:00",
        "fecha_de_compra": "2025-12-01T10:00:00",
        "id_comprobante": "no-es-int",
    }
    s = PedidoArregloCreateSerializer(data=data)
    assert not s.is_valid()
    assert "id_comprobante" in s.errors


# ---------------------------------------------------------------------------
# Transiciones de estado
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_transiciones_admin_todas(django_user_model):
    user = django_user_model.objects.create_user(username="admin1", password="pw")
    _add_group(user, "arreglos_admin")
    trans = _get_transiciones_permitidas(user, EstadoArreglo.BORRADOR)
    valores = [e.value for e in trans]
    assert EstadoArreglo.ENVIADO in valores
    assert EstadoArreglo.TERMINADO_IAF in valores


@pytest.mark.django_db
def test_transiciones_operador_todas(django_user_model):
    user = django_user_model.objects.create_user(username="op1", password="pw")
    _add_group(user, "arreglos_operador")
    trans = _get_transiciones_permitidas(user, EstadoArreglo.BORRADOR)
    assert len(trans) > 1


@pytest.mark.django_db
def test_transiciones_emisor_borrador_a_enviado(django_user_model):
    user = django_user_model.objects.create_user(username="emisor1", password="pw")
    _add_group(user, "arreglos_emisor")
    trans = _get_transiciones_permitidas(user, EstadoArreglo.BORRADOR)
    valores = [e.value for e in trans]
    assert EstadoArreglo.ENVIADO in valores
    # No puede ir a FABRICA directamente
    assert EstadoArreglo.FABRICA not in valores


@pytest.mark.django_db
def test_transiciones_emisor_desde_no_borrador_vacia(django_user_model):
    user = django_user_model.objects.create_user(username="emisor2", password="pw")
    _add_group(user, "arreglos_emisor")
    trans = _get_transiciones_permitidas(user, EstadoArreglo.FABRICA)
    assert trans == []


@pytest.mark.django_db
def test_transiciones_fabrica(django_user_model):
    user = django_user_model.objects.create_user(username="fab1", password="pw")
    _add_group(user, "arreglos_fabrica")
    # ENVIADO → FABRICA
    trans = _get_transiciones_permitidas(user, EstadoArreglo.ENVIADO)
    valores = [e.value for e in trans]
    assert EstadoArreglo.FABRICA in valores
    assert EstadoArreglo.TERMINADO_R not in valores


@pytest.mark.django_db
def test_transiciones_deposito_reparados(django_user_model):
    user = django_user_model.objects.create_user(username="dep1", password="pw")
    _add_group(user, "arreglos_deposito")
    trans = _get_transiciones_permitidas(user, EstadoArreglo.REPARADOS)
    valores = [e.value for e in trans]
    assert EstadoArreglo.TERMINADO_R in valores
    assert EstadoArreglo.TERMINADO_IAF in valores


@pytest.mark.django_db
def test_transiciones_consultor_vacio(django_user_model):
    user = django_user_model.objects.create_user(username="cons1", password="pw")
    _add_group(user, "arreglos_consultor")
    trans = _get_transiciones_permitidas(user, EstadoArreglo.BORRADOR)
    assert trans == []


# ---------------------------------------------------------------------------
# Permisos de creación/edición
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_puede_crear_emisor(django_user_model):
    user = django_user_model.objects.create_user(username="e1", password="pw")
    _add_group(user, "arreglos_emisor")
    assert _puede_crear(user) is True


@pytest.mark.django_db
def test_puede_crear_consultor_no(django_user_model):
    user = django_user_model.objects.create_user(username="c1", password="pw")
    _add_group(user, "arreglos_consultor")
    assert _puede_crear(user) is False


@pytest.mark.django_db
def test_puede_editar_solo_admin_operador(django_user_model):
    admin = django_user_model.objects.create_user(username="a1", password="pw")
    _add_group(admin, "arreglos_admin")
    emisor = django_user_model.objects.create_user(username="em1", password="pw")
    _add_group(emisor, "arreglos_emisor")
    assert _puede_editar(admin) is True
    assert _puede_editar(emisor) is False


# ---------------------------------------------------------------------------
# URLs: resolución (import check)
# ---------------------------------------------------------------------------

def test_arreglos_urls_import():
    from arreglos.urls import urlpatterns
    names = [p.name for p in urlpatterns if hasattr(p, "name")]
    # Router genera URLs sin name en este nivel; verificamos vistas directas
    assert any("pedido" in str(p.pattern) or "api" in str(p.pattern) for p in urlpatterns)
