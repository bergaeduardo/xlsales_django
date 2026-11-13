"""Tests US #974 — arreglos/models.py (EstadoArreglo, PedidoArreglo, DetalleArticuloArreglo, ChatArreglo)."""
import pytest
from django.db import models

from arreglos.models import (
    ChatArreglo,
    DetalleArticuloArreglo,
    EstadoArreglo,
    PedidoArreglo,
)


# ---------------------------------------------------------------------------
# EstadoArreglo (IntegerChoices) — sin DB
# ---------------------------------------------------------------------------

def test_estado_arreglo_es_integer_choices():
    assert issubclass(EstadoArreglo, models.IntegerChoices)


def test_estado_arreglo_tiene_10_valores():
    assert len(EstadoArreglo.choices) == 10


def test_estado_arreglo_valores_correctos():
    assert EstadoArreglo.BORRADOR == 0
    assert EstadoArreglo.ENVIADO == 1
    assert EstadoArreglo.FABRICA == 2
    assert EstadoArreglo.REPARACION == 3
    assert EstadoArreglo.REPARADOS == 4
    assert EstadoArreglo.TERMINADO_R == 5
    assert EstadoArreglo.FINALIZADO == 6
    assert EstadoArreglo.IMPORTE_A_FAVOR == 7
    assert EstadoArreglo.NC_OTORGADA == 8
    assert EstadoArreglo.TERMINADO_IAF == 9


def test_estado_arreglo_labels():
    assert EstadoArreglo(0).label == "Borrador"
    assert EstadoArreglo(6).label == "Finalizado"


# ---------------------------------------------------------------------------
# PedidoArreglo — estructura (sin DB, managed=False)
# ---------------------------------------------------------------------------

def test_pedido_arreglo_managed_false():
    assert PedidoArreglo._meta.managed is False


def test_pedido_arreglo_db_table():
    assert PedidoArreglo._meta.db_table == "Pedidoes"


def test_pedido_arreglo_app_label():
    assert PedidoArreglo._meta.app_label == "arreglos"


def test_pedido_arreglo_ordering():
    assert PedidoArreglo._meta.ordering == ["-id"]


def test_pedido_arreglo_pk_es_autoint():
    pk_field = PedidoArreglo._meta.get_field("id")
    assert isinstance(pk_field, models.AutoField)
    assert pk_field.db_column == "Id"


def test_pedido_arreglo_estado_usa_choices():
    field = PedidoArreglo._meta.get_field("estado")
    assert field.choices == EstadoArreglo.choices


def test_pedido_arreglo_6_booleans_con_default_false():
    """F1: todos los BooleanFields tienen default=False."""
    bool_fields = ["forro", "cierre", "costura", "correa", "herraje", "otro"]
    for nombre in bool_fields:
        field = PedidoArreglo._meta.get_field(nombre)
        assert isinstance(field, models.BooleanField), f"{nombre} no es BooleanField"
        assert field.default is False, f"{nombre}.default debe ser False"


def test_pedido_arreglo_db_columns_booleans():
    expected = {
        "forro": "Forro", "cierre": "Cierre", "costura": "Costura",
        "correa": "Correa", "herraje": "Herraje", "otro": "Otro",
    }
    for attr, col in expected.items():
        field = PedidoArreglo._meta.get_field(attr)
        assert field.db_column == col, f"{attr}.db_column debe ser {col!r}"


def test_pedido_arreglo_str():
    p = PedidoArreglo.__new__(PedidoArreglo)
    p.id = 42
    p.cliente = "Juan Pérez"
    assert str(p) == "Pedido #42 — Juan Pérez"


def test_pedido_arreglo_str_sin_cliente():
    p = PedidoArreglo.__new__(PedidoArreglo)
    p.id = 1
    p.cliente = None
    assert str(p) == "Pedido #1 — s/d"


def test_pedido_arreglo_tiene_historical_records():
    """HistoricalRecords agrega campo history al modelo."""
    assert hasattr(PedidoArreglo, "history")


# ---------------------------------------------------------------------------
# DetalleArticuloArreglo — estructura
# ---------------------------------------------------------------------------

def test_detalle_managed_false():
    assert DetalleArticuloArreglo._meta.managed is False


def test_detalle_db_table():
    assert DetalleArticuloArreglo._meta.db_table == "DetalleArticulo"


def test_detalle_ordering():
    """F3: ordering por id_detalle_articulo."""
    assert DetalleArticuloArreglo._meta.ordering == ["id_detalle_articulo"]


def test_detalle_pk_db_column():
    pk = DetalleArticuloArreglo._meta.get_field("id_detalle_articulo")
    assert isinstance(pk, models.AutoField)
    assert pk.db_column == "IdDetalleArticulo"


def test_detalle_fk_pedido_protect_no_constraint():
    """F2: on_delete=PROTECT, db_constraint=False."""
    fk = DetalleArticuloArreglo._meta.get_field("pedido")
    assert fk.remote_field.on_delete is models.PROTECT
    assert fk.db_constraint is False


def test_detalle_fk_db_column():
    fk = DetalleArticuloArreglo._meta.get_field("pedido")
    assert fk.column == "IdPedido"


def test_detalle_str():
    d = DetalleArticuloArreglo(codigo_articulo="ART-001", pedido_id=7)
    assert str(d) == "ART-001 (pedido #7)"


def test_detalle_str_sin_codigo():
    d = DetalleArticuloArreglo(codigo_articulo=None, pedido_id=3)
    assert str(d) == "s/d (pedido #3)"


def test_detalle_tiene_historical_records():
    assert hasattr(DetalleArticuloArreglo, "history")


# ---------------------------------------------------------------------------
# ChatArreglo — estructura
# ---------------------------------------------------------------------------

def test_chat_managed_false():
    assert ChatArreglo._meta.managed is False


def test_chat_db_table():
    assert ChatArreglo._meta.db_table == "Chats"


def test_chat_ordering():
    assert ChatArreglo._meta.ordering == ["fecha"]


def test_chat_pk_bigautofield():
    pk = ChatArreglo._meta.get_field("id")
    assert isinstance(pk, models.BigAutoField)
    assert pk.db_column == "Id"


def test_chat_fk_pedido_protect_no_constraint():
    """F2: on_delete=PROTECT, db_constraint=False."""
    fk = ChatArreglo._meta.get_field("pedido")
    assert fk.remote_field.on_delete is models.PROTECT
    assert fk.db_constraint is False


def test_chat_fk_db_column():
    fk = ChatArreglo._meta.get_field("pedido")
    assert fk.column == "IdPedido"


def test_chat_str():
    c = ChatArreglo(id=99, pedido_id=5)
    assert str(c) == "Chat #99 (pedido #5)"


def test_chat_tiene_historical_records():
    assert hasattr(ChatArreglo, "history")


# ---------------------------------------------------------------------------
# Migración: check que no haya pendientes (falla si no existe migrations/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=["default", "xlsales", "tango"])
def test_migraciones_consistentes():
    """No deben existir migraciones pendientes para arreglos."""
    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    try:
        call_command(
            "makemigrations", "arreglos",
            "--check", "--dry-run",
            stdout=out, stderr=out,
        )
    except SystemExit as e:
        raise AssertionError(
            f"makemigrations --check salió con código {e.code}. "
            f"Hay migraciones pendientes para 'arreglos'. Output:\n{out.getvalue()}"
        )
