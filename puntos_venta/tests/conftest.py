"""
Fixtures compartidas para puntos_venta/tests/.

Override ROOT_URLCONF: la sidebar del template base usa {% url 'core:dashboard' %},
namespace que no está registrado aún en config/urls.py. El urls_test local lo
provee como stub para que los tests de vista puedan renderizar sin NoReverseMatch.
"""
import pytest


@pytest.fixture(autouse=True)
def use_test_urls(settings):
    settings.ROOT_URLCONF = "puntos_venta.tests.urls_test"
