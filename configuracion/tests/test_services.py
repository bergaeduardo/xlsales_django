import pytest
from django.core.cache import cache

from configuracion.models import ConfiguracionSistema, TipoDato
from configuracion.services import get_config


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_get_config_int_parse():
    ConfiguracionSistema.objects.create(clave="test.entero", valor="42", tipo=TipoDato.INT)
    result = get_config("test.entero")
    assert result == 42
    assert isinstance(result, int)


@pytest.mark.django_db
def test_get_config_missing_default():
    result = get_config("clave.inexistente", default="fallback")
    assert result == "fallback"


@pytest.mark.django_db
def test_get_config_missing_none():
    result = get_config("clave.inexistente")
    assert result is None


@pytest.mark.django_db
def test_get_config_bool_parse():
    ConfiguracionSistema.objects.create(clave="test.bool", valor="true", tipo=TipoDato.BOOL)
    assert get_config("test.bool") is True

    ConfiguracionSistema.objects.create(clave="test.bool2", valor="0", tipo=TipoDato.BOOL)
    assert get_config("test.bool2") is False


@pytest.mark.django_db
def test_get_config_cache_invalidation():
    cfg = ConfiguracionSistema.objects.create(clave="test.cache", valor="100", tipo=TipoDato.INT)
    assert get_config("test.cache") == 100

    cfg.valor = "200"
    cfg.save()  # dispara signal post_save → invalida cache

    assert get_config("test.cache") == 200
