"""Tests US #957 — ConfiguracionSistemaCreateForm / ConfiguracionSistemaUpdateForm."""
import pytest

from configuracion.forms import ConfiguracionSistemaCreateForm, ConfiguracionSistemaUpdateForm
from configuracion.models import ConfiguracionSistema, TipoDato


def _valid_create_data(**overrides):
    return {
        "clave": "test.version",
        "valor": "1.0.0",
        "tipo": TipoDato.STRING,
        "descripcion": "Versión de la app",
        "grupo": "app",
        "editable": True,
        **overrides,
    }


def _make(clave="existente", valor="valor", tipo=TipoDato.STRING, **kwargs):
    return ConfiguracionSistema.objects.create(clave=clave, valor=valor, tipo=tipo, **kwargs)


# --------------------------------------------------------------------------- #
# ConfiguracionSistemaCreateForm
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_create_form_valido():
    form = ConfiguracionSistemaCreateForm(data=_valid_create_data())
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_create_form_invalido_campos_requeridos():
    form = ConfiguracionSistemaCreateForm(data={})
    assert not form.is_valid()
    assert "clave" in form.errors
    assert "valor" in form.errors


@pytest.mark.django_db
def test_create_form_clave_duplicada():
    _make(clave="test.version")
    form = ConfiguracionSistemaCreateForm(data=_valid_create_data(clave="test.version"))
    assert not form.is_valid()
    assert "clave" in form.errors


@pytest.mark.django_db
def test_create_form_valor_invalido_para_tipo_int():
    form = ConfiguracionSistemaCreateForm(
        data=_valid_create_data(clave="app.numero", tipo=TipoDato.INT, valor="no-es-entero")
    )
    assert not form.is_valid()
    assert "valor" in form.errors


# --------------------------------------------------------------------------- #
# ConfiguracionSistemaUpdateForm — Meta.fields no expone clave ni tipo
# --------------------------------------------------------------------------- #

def test_update_form_no_expone_clave_ni_tipo():
    assert "clave" not in ConfiguracionSistemaUpdateForm.Meta.fields
    assert "tipo" not in ConfiguracionSistemaUpdateForm.Meta.fields


# --------------------------------------------------------------------------- #
# ConfiguracionSistemaUpdateForm — valida valor según instance.tipo
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
def test_update_form_int_valido():
    cfg = _make(clave="app.entero", valor="1", tipo=TipoDato.INT)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "42", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_update_form_int_invalido():
    cfg = _make(clave="app.entero", valor="1", tipo=TipoDato.INT)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "no-es-entero", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert not form.is_valid()
    assert "valor" in form.errors


@pytest.mark.django_db
def test_update_form_decimal_valido():
    cfg = _make(clave="app.decimal", valor="1.0", tipo=TipoDato.DECIMAL)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "99.99", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_update_form_decimal_invalido():
    cfg = _make(clave="app.decimal", valor="1.0", tipo=TipoDato.DECIMAL)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "no-es-decimal", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert not form.is_valid()
    assert "valor" in form.errors


@pytest.mark.django_db
def test_update_form_json_valido():
    cfg = _make(clave="app.json", valor="{}", tipo=TipoDato.JSON)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": '{"a": 1}', "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_update_form_json_invalido():
    cfg = _make(clave="app.json", valor="{}", tipo=TipoDato.JSON)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "{mal formado", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert not form.is_valid()
    assert "valor" in form.errors


@pytest.mark.django_db
def test_update_form_bool_valido():
    cfg = _make(clave="app.bool", valor="true", tipo=TipoDato.BOOL)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "false", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_update_form_bool_invalido():
    cfg = _make(clave="app.bool", valor="true", tipo=TipoDato.BOOL)
    form = ConfiguracionSistemaUpdateForm(
        data={"valor": "si", "descripcion": "", "grupo": "", "editable": True}, instance=cfg
    )
    assert not form.is_valid()
    assert "valor" in form.errors
