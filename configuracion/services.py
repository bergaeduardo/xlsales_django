import json
from decimal import Decimal

from django.core.cache import cache

from .models import ConfiguracionSistema, TipoDato

_CACHE_TIMEOUT = 300  # 5 minutos


def _parse(valor, tipo):
    if tipo == TipoDato.INT:
        return int(valor)
    if tipo == TipoDato.BOOL:
        return valor.lower() in {"true", "1"}
    if tipo == TipoDato.JSON:
        return json.loads(valor)
    if tipo == TipoDato.DECIMAL:
        return Decimal(valor)
    return valor  # string


def get_config(key, default=None):
    cache_key = f"configsys:{key}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        cfg = ConfiguracionSistema.objects.get(clave=key)
    except ConfiguracionSistema.DoesNotExist:
        return default
    valor = _parse(cfg.valor, cfg.tipo)
    cache.set(cache_key, valor, timeout=_CACHE_TIMEOUT)
    return valor
