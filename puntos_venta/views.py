from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import PuntoVentaForm
from .models import PuntoVenta


class PuntoVentaListView(LoginRequiredMixin, ListView):
    model = PuntoVenta
    template_name = "puntos_venta/list.html"
    context_object_name = "puntos_venta"
    paginate_by = 25

    def get_queryset(self):
        qs = PuntoVenta.objects.order_by("codigo")
        q = (self.request.GET.get("q") or "").strip()
        activo = (self.request.GET.get("activo") or "").strip()
        if q:
            qs = qs.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
        if activo == "1":
            qs = qs.filter(activo=True)
        elif activo == "0":
            qs = qs.filter(activo=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Puntos de Venta"
        ctx["q"] = self.request.GET.get("q", "")
        ctx["activo_actual"] = self.request.GET.get("activo", "")
        return ctx


class PuntoVentaCreateView(LoginRequiredMixin, CreateView):
    model = PuntoVenta
    form_class = PuntoVentaForm
    template_name = "puntos_venta/form.html"
    success_url = reverse_lazy("puntos_venta:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nuevo Punto de Venta"
        ctx["accion"] = "Crear"
        return ctx

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Punto de venta «{self.object.codigo}» creado correctamente.",
        )
        return response


class PuntoVentaUpdateView(LoginRequiredMixin, UpdateView):
    model = PuntoVenta
    form_class = PuntoVentaForm
    template_name = "puntos_venta/form.html"
    success_url = reverse_lazy("puntos_venta:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Editar — {self.object.codigo}"
        ctx["accion"] = "Guardar"
        return ctx

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Punto de venta «{self.object.codigo}» actualizado.",
        )
        return response


class PuntoVentaDeleteView(LoginRequiredMixin, DeleteView):
    """Soft-delete: desactiva el registro en lugar de borrarlo."""

    model = PuntoVenta
    template_name = "puntos_venta/delete_confirm.html"
    success_url = reverse_lazy("puntos_venta:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Desactivar — {self.object.codigo}"
        return ctx

    def form_valid(self, form):
        punto = self.object
        punto.activo = False
        punto.updated_by = self.request.user
        punto.save(update_fields=["activo", "updated_by", "updated_at"])
        messages.warning(
            self.request,
            f"Punto de venta «{punto.codigo}» desactivado.",
        )
        return HttpResponseRedirect(self.success_url)
