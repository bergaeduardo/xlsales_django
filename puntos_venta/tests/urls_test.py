"""
URL conf de test para puntos_venta.

Agrega stubs para los namespaces que el template base usa pero que aún no
están registrados en config/urls.py:
  - core:dashboard        (sidebar)
  - autenticacion:logout  (navbar dropdown)
"""
from django.urls import include, path
from django.views.generic import RedirectView

_stub = RedirectView.as_view(url="/", permanent=False)

core_urlpatterns = [
    path("", _stub, name="dashboard"),
]

autenticacion_urlpatterns = [
    path("logout/", _stub, name="logout"),
]

urlpatterns = [
    path("puntos-venta/", include("puntos_venta.urls")),
    path("core/", include((core_urlpatterns, "core"))),
    path("auth/", include((autenticacion_urlpatterns, "autenticacion"))),
]
