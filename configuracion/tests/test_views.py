"""Tests US #957 — ConfiguracionSistema CBV views."""
import pytest
from django.urls import reverse

from configuracion.models import ConfiguracionSistema, TipoDato

LIST_URL = reverse("configuracion:list")
CREATE_URL = reverse("configuracion:create")


def update_url(pk):
    return reverse("configuracion:update", kwargs={"pk": pk})


@pytest.fixture
def logged_client(client, django_user_model):
    user = django_user_model.objects.create_user(username="tester", password="pw")
    client.login(username="tester", password="pw")
    return client, user


def _make(clave="app.clave", valor="valor", tipo=TipoDato.STRING, **kwargs):
    return ConfiguracionSistema.objects.create(clave=clave, valor=valor, tipo=tipo, **kwargs)


# --------------------------------------------------------------------------- #
# Requiere login
# --------------------------------------------------------------------------- #

def test_list_requiere_login(client):
    response = client.get(LIST_URL)
    assert response.status_code == 302
    assert "login" in response["Location"]


def test_create_requiere_login(client):
    response = client.get(CREATE_URL)
    assert response.status_code == 302
    assert "login" in response["Location"]


@pytest.mark.django_db
def test_update_requiere_login(client):
    cfg = _make()
    response = client.get(update_url(cfg.pk))
    assert response.status_code == 302
    assert "login" in response["Location"]


# --------------------------------------------------------------------------- #
# List — filtros
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_list_filtro_q(logged_client):
    client, _ = logged_client
    _make(clave="test.version", descripcion="Versión de la app")
    _make(clave="test.nombre", descripcion="Nombre comercial")
    response = client.get(LIST_URL + "?q=version")
    assert response.status_code == 200
    claves = [c.clave for c in response.context["configuraciones"]]
    assert "test.version" in claves
    assert "test.nombre" not in claves


@pytest.mark.django_db
def test_list_filtro_grupo(logged_client):
    client, _ = logged_client
    _make(clave="test.tango.host", grupo="integracion.tango")
    _make(clave="test.version2", grupo="app")
    response = client.get(LIST_URL + "?grupo=tango")
    assert response.status_code == 200
    claves = [c.clave for c in response.context["configuraciones"]]
    assert "test.tango.host" in claves
    assert "test.version2" not in claves


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_create_post_valido(logged_client):
    client, user = logged_client
    response = client.post(
        CREATE_URL,
        {
            "clave": "test.version",
            "valor": "1.0.0",
            "tipo": TipoDato.STRING,
            "descripcion": "Versión",
            "grupo": "app",
            "editable": True,
        },
    )
    assert response.status_code == 302
    cfg = ConfiguracionSistema.objects.get(clave="test.version")
    assert cfg.valor == "1.0.0"
    assert cfg.created_by == user
    assert cfg.updated_by == user


# --------------------------------------------------------------------------- #
# Update
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_update_post_valido(logged_client):
    client, user = logged_client
    cfg = _make(clave="test.version", valor="1.0.0")
    response = client.post(
        update_url(cfg.pk),
        {"valor": "2.0.0", "descripcion": "", "grupo": "", "editable": True},
    )
    assert response.status_code == 302
    cfg.refresh_from_db()
    assert cfg.valor == "2.0.0"
    assert cfg.updated_by == user


@pytest.mark.django_db
def test_update_post_valor_invalido_para_tipo_no_cambia(logged_client):
    client, _ = logged_client
    cfg = _make(clave="app.entero", valor="1", tipo=TipoDato.INT)
    response = client.post(
        update_url(cfg.pk),
        {"valor": "no-es-entero", "descripcion": "", "grupo": "", "editable": True},
    )
    assert response.status_code == 200
    assert "valor" in response.context["form"].errors
    cfg.refresh_from_db()
    assert cfg.valor == "1"
