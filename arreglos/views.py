"""Views del módulo de Pedidos de Reparación (US #975)."""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from compartidos.permissions import (
    has_module_access,
    is_arreglos_admin,
    is_arreglos_consultor,
    is_arreglos_deposito,
    is_arreglos_emisor,
    is_arreglos_fabrica,
    is_arreglos_operador,
)

from .models import EstadoArreglo, PedidoArreglo
from .serializers import (
    CambiarEstadoSerializer,
    PedidoArregloCreateSerializer,
    PedidoArregloDetailSerializer,
    PedidoArregloListSerializer,
    PedidoArregloUpdateSerializer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transiciones de estado por rol
# ---------------------------------------------------------------------------
# Formato: estado_origen -> [estados_destino_permitidos]
_TRANSICIONES_EMISOR = {
    EstadoArreglo.BORRADOR: [EstadoArreglo.ENVIADO],
}
_TRANSICIONES_FABRICA = {
    EstadoArreglo.ENVIADO: [EstadoArreglo.FABRICA],
    EstadoArreglo.FABRICA: [EstadoArreglo.REPARACION],
    EstadoArreglo.REPARACION: [EstadoArreglo.REPARADOS],
}
_TRANSICIONES_DEPOSITO = {
    EstadoArreglo.REPARADOS: [EstadoArreglo.TERMINADO_R, EstadoArreglo.TERMINADO_IAF],
}


def _get_transiciones_permitidas(user, estado_actual):
    """Devuelve la lista de estados a los que el usuario puede transicionar desde estado_actual."""
    if is_arreglos_admin(user) or is_arreglos_operador(user):
        return [e for e in EstadoArreglo if e != estado_actual]
    destinos = set()
    if is_arreglos_emisor(user):
        destinos.update(_TRANSICIONES_EMISOR.get(estado_actual, []))
    if is_arreglos_fabrica(user):
        destinos.update(_TRANSICIONES_FABRICA.get(estado_actual, []))
    if is_arreglos_deposito(user):
        destinos.update(_TRANSICIONES_DEPOSITO.get(estado_actual, []))
    return list(destinos)


def _puede_crear(user):
    return is_arreglos_admin(user) or is_arreglos_operador(user) or is_arreglos_emisor(user)


def _puede_editar(user):
    return is_arreglos_admin(user) or is_arreglos_operador(user)


def _tiene_acceso_lectura(user):
    return has_module_access(user, "arreglos")


def _notificar_cambio_estado(pedido_id, estado_anterior, estado_nuevo, usuario_nombre):
    """Envía email de notificación de cambio de estado (llamar con on_commit)."""
    from django.core.mail import send_mail

    try:
        pedido = PedidoArreglo.objects.get(pk=pedido_id)
        if not pedido.email:
            return
        send_mail(
            subject=f"[XLSales] Pedido #{pedido_id} — estado actualizado",
            message=(
                f"Su pedido #{pedido_id} ha cambiado de estado:\n"
                f"  Anterior: {EstadoArreglo(estado_anterior).label}\n"
                f"  Nuevo:    {EstadoArreglo(estado_nuevo).label}\n\n"
                f"Actualizado por: {usuario_nombre}"
            ),
            from_email=None,
            recipient_list=[pedido.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Error enviando email para pedido #%s", pedido_id)


# ---------------------------------------------------------------------------
# API ViewSet
# ---------------------------------------------------------------------------

class PedidoArregloViewSet(viewsets.ModelViewSet):
    """ViewSet para Pedidos de Reparación."""

    permission_classes = [IsAuthenticated]
    queryset = PedidoArreglo.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PedidoArregloListSerializer
        if self.action == "create":
            return PedidoArregloCreateSerializer
        if self.action in ("update", "partial_update"):
            return PedidoArregloUpdateSerializer
        return PedidoArregloDetailSerializer

    def _check_modulo_access(self, user):
        if not _tiene_acceso_lectura(user):
            raise PermissionDenied("Sin acceso al módulo de arreglos.")

    def list(self, request, *args, **kwargs):
        self._check_modulo_access(request.user)
        qs = self.get_queryset()
        estado = request.query_params.get("estado")
        cliente = request.query_params.get("cliente")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        if estado is not None:
            qs = qs.filter(estado=estado)
        if cliente:
            qs = qs.filter(cliente__icontains=cliente)
        if fecha_desde:
            qs = qs.filter(fecha_solicitud__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_solicitud__date__lte=fecha_hasta)
        serializer = self.get_serializer(qs, many=True)
        return Response({"ok": True, "data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        self._check_modulo_access(request.user)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"ok": True, "data": serializer.data})

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not _puede_crear(request.user):
            return Response(
                {"ok": False, "error": "Sin permiso para crear pedidos."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"ok": False, "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = serializer.save()
        logger.info("Pedido #%s creado por %s", instance.pk, request.user)
        return Response(
            {"ok": True, "data": PedidoArregloDetailSerializer(instance).data},
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        if not _puede_editar(request.user):
            return Response(
                {"ok": False, "error": "Sin permiso para editar pedidos."},
                status=status.HTTP_403_FORBIDDEN,
            )
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {"ok": False, "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = serializer.save()
        logger.info("Pedido #%s actualizado por %s", instance.pk, request.user)
        return Response({"ok": True, "data": PedidoArregloDetailSerializer(instance).data})

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    @transaction.atomic
    def cambiar_estado(self, request, pk=None):
        self._check_modulo_access(request.user)
        instance = self.get_object()
        serializer = CambiarEstadoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"ok": False, "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nuevo_estado = serializer.validated_data["estado"]
        estado_actual = instance.estado
        permitidos = _get_transiciones_permitidas(request.user, estado_actual)
        if nuevo_estado not in [e.value for e in permitidos]:
            return Response(
                {
                    "ok": False,
                    "error": (
                        f"Transición no permitida: "
                        f"{EstadoArreglo(estado_actual).label} → {EstadoArreglo(nuevo_estado).label}"
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        instance.estado = nuevo_estado
        instance.save(update_fields=["estado"])
        logger.info(
            "Pedido #%s: estado %s→%s por %s",
            instance.pk, estado_actual, nuevo_estado, request.user,
        )
        transaction.on_commit(
            lambda: _notificar_cambio_estado(
                instance.pk, estado_actual, nuevo_estado,
                str(request.user),
            )
        )
        return Response({
            "ok": True,
            "data": {
                "id": instance.pk,
                "estado": nuevo_estado,
                "estado_display": EstadoArreglo(nuevo_estado).label,
            },
        })


# ---------------------------------------------------------------------------
# Vistas HTML (Tabler)
# ---------------------------------------------------------------------------

class ArreglosAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _tiene_acceso_lectura(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def pedido_list(request):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not _tiene_acceso_lectura(request.user):
        raise PermissionDenied

    qs = PedidoArreglo.objects.all()
    estado = request.GET.get("estado", "")
    cliente = request.GET.get("cliente", "")
    fecha_desde = request.GET.get("fecha_desde", "")
    fecha_hasta = request.GET.get("fecha_hasta", "")

    if estado != "":
        qs = qs.filter(estado=estado)
    if cliente:
        qs = qs.filter(cliente__icontains=cliente)
    if fecha_desde:
        qs = qs.filter(fecha_solicitud__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_solicitud__date__lte=fecha_hasta)

    return render(request, "arreglos/list.html", {
        "pedidos": qs,
        "estados": EstadoArreglo.choices,
        "filtro_estado": estado,
        "filtro_cliente": cliente,
        "filtro_fecha_desde": fecha_desde,
        "filtro_fecha_hasta": fecha_hasta,
        "puede_crear": _puede_crear(request.user),
        "puede_editar": _puede_editar(request.user),
    })


def pedido_detail(request, pk):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not _tiene_acceso_lectura(request.user):
        raise PermissionDenied

    pedido = get_object_or_404(PedidoArreglo, pk=pk)
    transiciones = _get_transiciones_permitidas(request.user, pedido.estado)
    history = pedido.history.all().order_by("-history_date")

    return render(request, "arreglos/detail.html", {
        "pedido": pedido,
        "detalles": pedido.detalles_articulo.all(),
        "chats": pedido.chats.all(),
        "history": history,
        "transiciones": transiciones,
        "puede_editar": _puede_editar(request.user),
        "estados": EstadoArreglo.choices,
    })


def pedido_create(request):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not _puede_crear(request.user):
        raise PermissionDenied

    from .forms import PedidoArregloForm
    if request.method == "POST":
        form = PedidoArregloForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                pedido = form.save(commit=False)
                pedido.estado = EstadoArreglo.BORRADOR
                pedido.save()
            messages.success(request, f"Pedido #{pedido.pk} creado correctamente.")
            return redirect(reverse("arreglos:detail", kwargs={"pk": pedido.pk}))
    else:
        form = PedidoArregloForm()

    return render(request, "arreglos/form.html", {
        "form": form,
        "titulo": "Nuevo Pedido de Arreglo",
        "accion": "Crear",
    })


def pedido_update(request, pk):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not _puede_editar(request.user):
        raise PermissionDenied

    pedido = get_object_or_404(PedidoArreglo, pk=pk)
    from .forms import PedidoArregloForm
    if request.method == "POST":
        form = PedidoArregloForm(request.POST, instance=pedido)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, f"Pedido #{pedido.pk} actualizado.")
            return redirect(reverse("arreglos:detail", kwargs={"pk": pedido.pk}))
    else:
        form = PedidoArregloForm(instance=pedido)

    return render(request, "arreglos/form.html", {
        "form": form,
        "pedido": pedido,
        "titulo": f"Editar Pedido #{pedido.pk}",
        "accion": "Guardar",
    })


def pedido_cambiar_estado(request, pk):
    """Vista POST para cambio de estado desde el formulario HTML."""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if not _tiene_acceso_lectura(request.user):
        raise PermissionDenied
    if request.method != "POST":
        return redirect(reverse("arreglos:detail", kwargs={"pk": pk}))

    pedido = get_object_or_404(PedidoArreglo, pk=pk)
    nuevo_estado_str = request.POST.get("estado")
    try:
        nuevo_estado = int(nuevo_estado_str)
    except (TypeError, ValueError):
        messages.error(request, "Estado inválido.")
        return redirect(reverse("arreglos:detail", kwargs={"pk": pk}))

    estado_actual = pedido.estado
    permitidos = _get_transiciones_permitidas(request.user, estado_actual)
    if nuevo_estado not in [e.value for e in permitidos]:
        messages.error(
            request,
            f"Transición no permitida: "
            f"{EstadoArreglo(estado_actual).label} → {EstadoArreglo(nuevo_estado).label}",
        )
        return redirect(reverse("arreglos:detail", kwargs={"pk": pk}))

    with transaction.atomic():
        pedido.estado = nuevo_estado
        pedido.save(update_fields=["estado"])
        transaction.on_commit(
            lambda: _notificar_cambio_estado(
                pedido.pk, estado_actual, nuevo_estado, str(request.user)
            )
        )

    logger.info(
        "Pedido #%s: estado %s→%s por %s",
        pedido.pk, estado_actual, nuevo_estado, request.user,
    )
    messages.success(
        request,
        f"Estado actualizado a: {EstadoArreglo(nuevo_estado).label}",
    )
    return redirect(reverse("arreglos:detail", kwargs={"pk": pk}))
