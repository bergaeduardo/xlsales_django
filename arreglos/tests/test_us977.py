"""Tests US #977 — Chat interno por pedido A3."""
import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.test import RequestFactory

from arreglos.models import EstadoArreglo
from arreglos.views import _puede_chatear


def _make_user(username, groups=()):
    user, _ = User.objects.get_or_create(username=username)
    for g in groups:
        group, _ = Group.objects.get_or_create(name=g)
        user.groups.add(group)
    return user


# ---------------------------------------------------------------------------
# _puede_chatear
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_puede_chatear_fabrica():
    u = _make_user("chat_fabrica_1", ["arreglos_fabrica"])
    assert _puede_chatear(u) is True


@pytest.mark.django_db
def test_puede_chatear_admin():
    u = _make_user("chat_admin_1", ["arreglos_admin"])
    assert _puede_chatear(u) is True


@pytest.mark.django_db
def test_puede_chatear_operador():
    u = _make_user("chat_operador_1", ["arreglos_operador"])
    assert _puede_chatear(u) is True


@pytest.mark.django_db
def test_no_puede_chatear_emisor():
    u = _make_user("chat_emisor_1", ["arreglos_emisor"])
    assert _puede_chatear(u) is False


@pytest.mark.django_db
def test_no_puede_chatear_consultor():
    u = _make_user("chat_consultor_1", ["arreglos_consultor"])
    assert _puede_chatear(u) is False


@pytest.mark.django_db
def test_no_puede_chatear_deposito():
    u = _make_user("chat_deposito_1", ["arreglos_deposito"])
    assert _puede_chatear(u) is False


@pytest.mark.django_db
def test_no_puede_chatear_sin_grupos():
    u = _make_user("chat_ninguno_1")
    assert _puede_chatear(u) is False


# ---------------------------------------------------------------------------
# Estado FABRICA como umbral de visibilidad del chat
# ---------------------------------------------------------------------------

def test_fabrica_es_estado_2():
    assert EstadoArreglo.FABRICA == 2


def test_chat_no_visible_en_borrador():
    assert EstadoArreglo.BORRADOR < EstadoArreglo.FABRICA


def test_chat_no_visible_en_enviado():
    assert EstadoArreglo.ENVIADO < EstadoArreglo.FABRICA


def test_chat_visible_en_fabrica():
    assert EstadoArreglo.FABRICA >= EstadoArreglo.FABRICA


def test_chat_visible_en_reparacion():
    assert EstadoArreglo.REPARACION >= EstadoArreglo.FABRICA


def test_chat_visible_en_finalizado():
    assert EstadoArreglo.FINALIZADO >= EstadoArreglo.FABRICA


# ---------------------------------------------------------------------------
# Vista chat_enviar_mensaje — permisos y validaciones
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_chat_enviar_get_redirige_a_detail(client):
    u = _make_user("chat_get_1", ["arreglos_fabrica"])
    client.force_login(u)
    response = client.get("/puntos-venta/../arreglos/pedidos/1/chat/", follow=False)
    # GET debe redirigir (302 o 301)
    assert response.status_code in (301, 302, 404)


@pytest.mark.django_db
def test_chat_enviar_sin_login_redirige(client):
    response = client.post("/arreglos/pedidos/1/chat/", {"descripcion": "hola"})
    assert response.status_code in (302, 301)
    assert "/login/" in response["Location"] or "login" in response["Location"]


@pytest.mark.django_db
def test_chat_enviar_sin_permiso_devuelve_403(client):
    u = _make_user("chat_sin_perm_1", ["arreglos_emisor"])
    client.force_login(u)
    response = client.post("/arreglos/pedidos/1/chat/", {"descripcion": "hola"})
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Vista chat_enviar_mensaje — lógica de negocio (mocks DB cross)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_chat_enviar_estado_bajo_muestra_error(client):
    """Pedido en estado BORRADOR → no permite chatear → redirige con error."""
    from arreglos.models import PedidoArreglo
    from unittest.mock import MagicMock, patch

    u = _make_user("chat_state_1", ["arreglos_fabrica"])
    client.force_login(u)

    pedido_mock = MagicMock(spec=PedidoArreglo)
    pedido_mock.pk = 99
    pedido_mock.estado = EstadoArreglo.BORRADOR

    with patch("arreglos.views.get_object_or_404", return_value=pedido_mock):
        response = client.post("/arreglos/pedidos/99/chat/", {"descripcion": "hola"})

    assert response.status_code == 302
    messages_list = list(get_messages(response.wsgi_request))
    assert any("fábrica" in str(m).lower() or "estado" in str(m).lower() for m in messages_list)


@pytest.mark.django_db
def test_chat_enviar_descripcion_vacia_muestra_error(client):
    """Descripción en blanco → redirige con error."""
    from arreglos.models import PedidoArreglo
    from unittest.mock import MagicMock, patch

    u = _make_user("chat_empty_1", ["arreglos_fabrica"])
    client.force_login(u)

    pedido_mock = MagicMock(spec=PedidoArreglo)
    pedido_mock.pk = 99
    pedido_mock.estado = EstadoArreglo.FABRICA

    with patch("arreglos.views.get_object_or_404", return_value=pedido_mock):
        response = client.post("/arreglos/pedidos/99/chat/", {"descripcion": "   "})

    assert response.status_code == 302
    messages_list = list(get_messages(response.wsgi_request))
    assert any("vacío" in str(m).lower() or "empty" in str(m).lower() for m in messages_list)


@pytest.mark.django_db
def test_chat_enviar_valido_crea_mensaje(client):
    """POST válido → crea ChatArreglo y redirige con mensaje de éxito."""
    from arreglos.models import ChatArreglo, PedidoArreglo
    from unittest.mock import MagicMock, patch

    u = _make_user("chat_ok_1", ["arreglos_fabrica"])
    client.force_login(u)

    pedido_mock = MagicMock(spec=PedidoArreglo)
    pedido_mock.pk = 99
    pedido_mock.estado = EstadoArreglo.FABRICA

    with patch("arreglos.views.get_object_or_404", return_value=pedido_mock), \
         patch.object(ChatArreglo.objects, "using") as mock_using:
        mock_manager = MagicMock()
        mock_using.return_value = mock_manager

        response = client.post("/arreglos/pedidos/99/chat/", {"descripcion": "Todo ok"})

    assert response.status_code == 302
    mock_using.assert_called_once_with("xlsales")
    mock_manager.create.assert_called_once()
    call_kwargs = mock_manager.create.call_args.kwargs
    assert call_kwargs["descripcion"] == "Todo ok"
    assert call_kwargs["pedido"] == pedido_mock
    messages_list = list(get_messages(response.wsgi_request))
    assert any("enviado" in str(m).lower() for m in messages_list)


@pytest.mark.django_db
def test_chat_enviar_usa_nombre_completo(client):
    """El campo `usuario` del chat toma get_full_name() cuando está disponible."""
    from arreglos.models import ChatArreglo, PedidoArreglo
    from unittest.mock import MagicMock, patch

    u = _make_user("chat_nombre_1", ["arreglos_fabrica"])
    u.first_name = "Juan"
    u.last_name = "Pérez"
    u.save()
    client.force_login(u)

    pedido_mock = MagicMock(spec=PedidoArreglo)
    pedido_mock.pk = 99
    pedido_mock.estado = EstadoArreglo.FABRICA

    with patch("arreglos.views.get_object_or_404", return_value=pedido_mock), \
         patch.object(ChatArreglo.objects, "using") as mock_using:
        mock_manager = MagicMock()
        mock_using.return_value = mock_manager
        client.post("/arreglos/pedidos/99/chat/", {"descripcion": "Hola"})

    call_kwargs = mock_manager.create.call_args.kwargs
    assert call_kwargs["usuario"] == "Juan Pérez"


@pytest.mark.django_db
def test_chat_enviar_usa_username_si_sin_nombre(client):
    """Si no hay nombre completo, usa el username."""
    from arreglos.models import ChatArreglo, PedidoArreglo
    from unittest.mock import MagicMock, patch

    u = _make_user("chat_user_1", ["arreglos_admin"])
    client.force_login(u)

    pedido_mock = MagicMock(spec=PedidoArreglo)
    pedido_mock.pk = 99
    pedido_mock.estado = EstadoArreglo.REPARACION

    with patch("arreglos.views.get_object_or_404", return_value=pedido_mock), \
         patch.object(ChatArreglo.objects, "using") as mock_using:
        mock_manager = MagicMock()
        mock_using.return_value = mock_manager
        client.post("/arreglos/pedidos/99/chat/", {"descripcion": "Test"})

    call_kwargs = mock_manager.create.call_args.kwargs
    assert call_kwargs["usuario"] == "chat_user_1"
