"""URLs para el módulo de Pedidos de Reparación (US #975)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PedidoArregloViewSet,
    pedido_cambiar_estado,
    pedido_create,
    pedido_detail,
    pedido_list,
    pedido_update,
)

app_name = "arreglos"

router = DefaultRouter()
router.register(r"api/pedidos", PedidoArregloViewSet, basename="api-pedido")

urlpatterns = [
    path("", include(router.urls)),
    path("pedidos/", pedido_list, name="list"),
    path("pedidos/nuevo/", pedido_create, name="create"),
    path("pedidos/<int:pk>/", pedido_detail, name="detail"),
    path("pedidos/<int:pk>/editar/", pedido_update, name="update"),
    path("pedidos/<int:pk>/cambiar-estado/", pedido_cambiar_estado, name="cambiar_estado"),
]
