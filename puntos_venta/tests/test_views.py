"""Tests US #956 — PuntoVenta CBV views."""
import pytest
from django.urls import reverse

from puntos_venta.models import PuntoVenta

LIST_URL = reverse("puntos_venta:list")
CREATE_URL = reverse("puntos_venta:create")


def update_url(pk):
    return reverse("puntos_venta:update", kwargs={"pk": pk})


def delete_url(pk):
    return reverse("puntos_venta:delete", kwargs={"pk": pk})


@pytest.fixture
def logged_client(client, django_user_model):
    user = django_user_model.objects.create_user(username="tester", password="pw")
    client.login(username="tester", password="pw")
    return client, user


def _make(codigo="VTA001", nombre="Venta Central", **kwargs):
    return PuntoVenta.objects.create(codigo=codigo, nombre=nombre, **kwargs)


# --------------------------------------------------------------------------- #
# Test 12 — list requires_login
# --------------------------------------------------------------------------- #

def test_list_requires_login(client):
    response = client.get(LIST_URL)
    assert response.status_code == 302
    assert "/login/" in response["Location"] or "login" in response["Location"]


# --------------------------------------------------------------------------- #
# Test 13 — list paginated
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_list_paginado_25(logged_client):
    client, _ = logged_client
    for i in range(30):
        _make(codigo=f"V{i:03d}", nombre=f"PV {i}")
    response = client.get(LIST_URL)
    assert response.status_code == 200
    page_obj = response.context["page_obj"]
    assert len(page_obj.object_list) == 25


# --------------------------------------------------------------------------- #
# Test 14 — create sets created_by
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_create_setea_created_by(logged_client):
    client, user = logged_client
    response = client.post(
        CREATE_URL,
        {"codigo": "VTA001", "nombre": "Venta Central", "activo": True},
    )
    assert response.status_code == 302
    pv = PuntoVenta.objects.get(codigo="VTA001")
    assert pv.created_by == user


# --------------------------------------------------------------------------- #
# Test 15 — update sets updated_by
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_update_setea_updated_by(logged_client):
    client, user = logged_client
    pv = _make(codigo="VTA002", nombre="Original")
    response = client.post(
        update_url(pv.pk),
        {"codigo": "VTA002", "nombre": "Modificado", "activo": True},
    )
    assert response.status_code == 302
    pv.refresh_from_db()
    assert pv.updated_by == user
    assert pv.nombre == "Modificado"


# --------------------------------------------------------------------------- #
# Test 16 — delete is soft (POST → redirect → activo=False, registro existe)
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_delete_is_soft(logged_client):
    client, _ = logged_client
    pv = _make(codigo="VTA003", nombre="A Desactivar")
    response = client.post(delete_url(pv.pk))
    assert response.status_code == 302
    pv.refresh_from_db()
    assert pv.activo is False
    assert PuntoVenta.objects.filter(pk=pv.pk).exists()


# --------------------------------------------------------------------------- #
# Test 17 — delete 404 con pk inexistente
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_delete_404_pk_inexistente(logged_client):
    client, _ = logged_client
    response = client.post(delete_url(99999))
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Extra — context_data y filtros (cobertura views ≥85%)
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_list_filtro_q(logged_client):
    """Filtrar por ?q= reduce el queryset."""
    client, _ = logged_client
    _make(codigo="ALFA", nombre="Alfa Sucursal")
    _make(codigo="BETA", nombre="Beta Sucursal")
    response = client.get(LIST_URL + "?q=ALFA")
    assert response.status_code == 200
    assert len(response.context["page_obj"].object_list) == 1


@pytest.mark.django_db
def test_list_filtro_activo(logged_client):
    """Filtrar por ?activo=0 muestra solo inactivos."""
    client, _ = logged_client
    _make(codigo="ACT01", nombre="Activo")
    _make(codigo="INA01", nombre="Inactivo", activo=False)
    response = client.get(LIST_URL + "?activo=0")
    assert response.status_code == 200
    codigos = [pv.codigo for pv in response.context["page_obj"].object_list]
    assert "INA01" in codigos
    assert "ACT01" not in codigos


@pytest.mark.django_db
def test_create_get_context(logged_client):
    """GET en create devuelve 200 con titulo y accion en contexto."""
    client, _ = logged_client
    response = client.get(CREATE_URL)
    assert response.status_code == 200
    assert response.context["titulo"] == "Nuevo Punto de Venta"
    assert response.context["accion"] == "Crear"


@pytest.mark.django_db
def test_update_get_context(logged_client):
    """GET en update devuelve 200 con titulo correcto."""
    client, _ = logged_client
    pv = _make(codigo="CTX01", nombre="Test Ctx")
    response = client.get(update_url(pv.pk))
    assert response.status_code == 200
    assert "CTX01" in response.context["titulo"]


@pytest.mark.django_db
def test_delete_get_context(logged_client):
    """GET en delete devuelve 200 con titulo correcto."""
    client, _ = logged_client
    pv = _make(codigo="DEL01", nombre="A Desactivar")
    response = client.get(delete_url(pv.pk))
    assert response.status_code == 200
    assert "DEL01" in response.context["titulo"]
