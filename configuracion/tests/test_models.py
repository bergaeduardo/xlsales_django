"""Tests US #957 — ConfiguracionSistema model."""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from configuracion.models import ConfiguracionSistema, TipoDato


def _make(clave="test.clave", valor="valor", tipo=TipoDato.STRING, **kwargs):
    return ConfiguracionSistema.objects.create(clave=clave, valor=valor, tipo=tipo, **kwargs)


# --------------------------------------------------------------------------- #
# Creación válida + __str__
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_crear_valido():
    cfg = _make(clave="test.version", valor="1.0.0")
    assert cfg.pk is not None
    assert cfg.tipo == TipoDato.STRING
    assert cfg.editable is True


@pytest.mark.django_db
def test_str_incluye_clave_y_valor_truncado():
    cfg = _make(clave="test.version", valor="1.0.0")
    assert str(cfg) == "test.version = 1.0.0"


@pytest.mark.django_db
def test_str_trunca_valor_a_40_caracteres():
    valor_largo = "x" * 100
    cfg = _make(clave="test.largo", valor=valor_largo)
    assert str(cfg) == f"test.largo = {valor_largo[:40]}"


# --------------------------------------------------------------------------- #
# Uniqueness de clave
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_clave_unique():
    _make(clave="app.unica")
    with pytest.raises(IntegrityError):
        _make(clave="app.unica")


# --------------------------------------------------------------------------- #
# clean() — STRING (sin validación especial, siempre válido)
# --------------------------------------------------------------------------- #

def test_clean_string_siempre_valido():
    cfg = ConfiguracionSistema(clave="x", valor="cualquier texto", tipo=TipoDato.STRING)
    cfg.clean()  # no debe lanzar


# --------------------------------------------------------------------------- #
# clean() — INT
# --------------------------------------------------------------------------- #

def test_clean_int_valido():
    cfg = ConfiguracionSistema(clave="x", valor="42", tipo=TipoDato.INT)
    cfg.clean()  # no debe lanzar


def test_clean_int_invalido():
    cfg = ConfiguracionSistema(clave="x", valor="no-es-entero", tipo=TipoDato.INT)
    with pytest.raises(ValidationError) as exc:
        cfg.clean()
    assert "valor" in exc.value.message_dict


# --------------------------------------------------------------------------- #
# clean() — DECIMAL
# --------------------------------------------------------------------------- #

def test_clean_decimal_valido():
    cfg = ConfiguracionSistema(clave="x", valor="10.50", tipo=TipoDato.DECIMAL)
    cfg.clean()  # no debe lanzar


def test_clean_decimal_invalido():
    cfg = ConfiguracionSistema(clave="x", valor="no-es-decimal", tipo=TipoDato.DECIMAL)
    with pytest.raises(ValidationError) as exc:
        cfg.clean()
    assert "valor" in exc.value.message_dict


# --------------------------------------------------------------------------- #
# clean() — JSON
# --------------------------------------------------------------------------- #

def test_clean_json_valido():
    cfg = ConfiguracionSistema(clave="x", valor='{"a": 1}', tipo=TipoDato.JSON)
    cfg.clean()  # no debe lanzar


def test_clean_json_invalido():
    cfg = ConfiguracionSistema(clave="x", valor="{mal formado", tipo=TipoDato.JSON)
    with pytest.raises(ValidationError) as exc:
        cfg.clean()
    assert "valor" in exc.value.message_dict


# --------------------------------------------------------------------------- #
# clean() — BOOL
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("valor", ["true", "false", "1", "0", "TRUE", "False"])
def test_clean_bool_valido(valor):
    cfg = ConfiguracionSistema(clave="x", valor=valor, tipo=TipoDato.BOOL)
    cfg.clean()  # no debe lanzar


def test_clean_bool_invalido():
    cfg = ConfiguracionSistema(clave="x", valor="si", tipo=TipoDato.BOOL)
    with pytest.raises(ValidationError) as exc:
        cfg.clean()
    assert "valor" in exc.value.message_dict
