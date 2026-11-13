from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

autenticacion_urls = (
    [
        path("logout/", auth_views.LogoutView.as_view(), name="logout"),
        path("login/", auth_views.LoginView.as_view(), name="login"),
    ],
    "autenticacion",
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("auth/", include(autenticacion_urls)),
    # F1+: compartidos, arreglos, cads
    path("puntos-venta/", include("puntos_venta.urls")),
    path("configuracion/", include("configuracion.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
