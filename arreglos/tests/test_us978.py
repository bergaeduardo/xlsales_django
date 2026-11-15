"""Tests US #978 — Notificaciones email por cambio de estado A4."""
from unittest.mock import MagicMock, patch, call

import pytest
from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings

from arreglos.models import EstadoArreglo, PedidoArreglo
from arreglos.views import _notificar_cambio_estado


def _make_user(username, groups=()):
    user, _ = User.objects.get_or_create(username=username)
    for g in groups:
        group, _ = Group.objects.get_or_create(name=g)
        user.groups.add(group)
    return user


# ---------------------------------------------------------------------------
# _notificar_cambio_estado — lógica directa (sin HTTP)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_notificar_envia_email_cuando_hay_email():
    """Pedido con email → send_mail llamado con el asunto correcto."""
    pedido = MagicMock(spec=PedidoArreglo)
    pedido.pk = 42
    pedido.email = "cliente@test.com"

    with patch("arreglos.views.PedidoArreglo.objects") as mock_mgr, \
         patch("arreglos.views.send_mail") as mock_mail:
        mock_mgr.get.return_value = pedido

        _notificar_cambio_estado(42, EstadoArreglo.BORRADOR, EstadoArreglo.ENVIADO, "admin")

    mock_mail.assert_called_once()
    args, kwargs = mock_mail.call_args
    subject = args[0] if args else kwargs.get("subject", "")
    assert "42" in subject
    assert kwargs.get("recipient_list") == ["cliente@test.com"]
    assert kwargs.get("fail_silently") is True


@pytest.mark.django_db
def test_notificar_no_envia_si_sin_email():
    """Pedido sin email → send_mail NO llamado."""
    pedido = MagicMock(spec=PedidoArreglo)
    pedido.pk = 43
    pedido.email = ""

    with patch("arreglos.views.PedidoArreglo.objects") as mock_mgr, \
         patch("arreglos.views.send_mail") as mock_mail:
        mock_mgr.get.return_value = pedido

        _notificar_cambio_estado(43, EstadoArreglo.BORRADOR, EstadoArreglo.ENVIADO, "admin")

    mock_mail.assert_not_called()


@pytest.mark.django_db
def test_notificar_no_envia_si_email_none():
    """Pedido con email=None → send_mail NO llamado."""
    pedido = MagicMock(spec=PedidoArreglo)
    pedido.pk = 44
    pedido.email = None

    with patch("arreglos.views.PedidoArreglo.objects") as mock_mgr, \
         patch("arreglos.views.send_mail") as mock_mail:
        mock_mgr.get.return_value = pedido

        _notificar_cambio_estado(44, EstadoArreglo.ENVIADO, EstadoArreglo.FABRICA, "operador")

    mock_mail.assert_not_called()


@pytest.mark.django_db
def test_notificar_incluye_estados_en_cuerpo():
    """El cuerpo del email menciona el estado anterior y el nuevo."""
    pedido = MagicMock(spec=PedidoArreglo)
    pedido.pk = 45
    pedido.email = "test@xl.com"

    with patch("arreglos.views.PedidoArreglo.objects") as mock_mgr, \
         patch("arreglos.views.send_mail") as mock_mail:
        mock_mgr.get.return_value = pedido

        _notificar_cambio_estado(
            45, EstadoArreglo.ENVIADO, EstadoArreglo.FABRICA, "Juan Pérez"
        )

    _, kwargs = mock_mail.call_args
    body = kwargs.get("message", "")
    assert EstadoArreglo(EstadoArreglo.ENVIADO).label in body
    assert EstadoArreglo(EstadoArreglo.FABRICA).label in body
    assert "Juan Pérez" in body


@pytest.mark.django_db
def test_notificar_silencia_excepciones():
    """Si send_mail lanza excepción, no propaga (fail_silently=True + try/except)."""
    pedido = MagicMock(spec=PedidoArreglo)
    pedido.pk = 46
    pedido.email = "test@xl.com"

    with patch("arreglos.views.PedidoArreglo.objects") as mock_mgr, \
         patch("arreglos.views.send_mail", side_effect=Exception("SMTP error")):
        mock_mgr.get.return_value = pedido
        # No debe propagar
        _notificar_cambio_estado(46, EstadoArreglo.BORRADOR, EstadoArreglo.ENVIADO, "x")


# ---------------------------------------------------------------------------
# Vista pedido_cambiar_estado — on_commit engancha la notificación
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cambiar_estado_html_programa_on_commit(client):
    """POST a cambiar-estado programa on_commit con _notificar_cambio_estado."""
    u = _make_user("operador_978", ["arreglos_operador"])
    client.force_login(u)

    pedido_mock = MagicMock(spec=PedidoArreglo)
    pedido_mock.pk = 99
    pedido_mock.estado = EstadoArreglo.ENVIADO

    estado_fab = MagicMock()
    estado_fab.value = EstadoArreglo.FABRICA

    captured = []

    with patch("arreglos.views.get_object_or_404", return_value=pedido_mock), \
         patch("arreglos.views._get_transiciones_permitidas", return_value=[estado_fab]), \
         patch("arreglos.views.transaction.on_commit", side_effect=lambda fn: captured.append(fn)), \
         patch("arreglos.views.transaction.atomic"):

        client.post("/arreglos/pedidos/99/cambiar-estado/", {"estado": str(EstadoArreglo.FABRICA)})

    assert len(captured) >= 1
