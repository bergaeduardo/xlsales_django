from django.urls import path

from .views import (
    PuntoVentaCreateView,
    PuntoVentaDeleteView,
    PuntoVentaListView,
    PuntoVentaUpdateView,
)

app_name = "puntos_venta"

urlpatterns = [
    path("", PuntoVentaListView.as_view(), name="list"),
    path("nuevo/", PuntoVentaCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", PuntoVentaUpdateView.as_view(), name="update"),
    path("<int:pk>/desactivar/", PuntoVentaDeleteView.as_view(), name="delete"),
]
