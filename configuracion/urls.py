from django.urls import path

from .views import ConfiguracionCreateView, ConfiguracionListView, ConfiguracionUpdateView

app_name = "configuracion"

urlpatterns = [
    path("", ConfiguracionListView.as_view(), name="list"),
    path("nueva/", ConfiguracionCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", ConfiguracionUpdateView.as_view(), name="update"),
]
