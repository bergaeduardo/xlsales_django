from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ConfiguracionSistemaCreateForm, ConfiguracionSistemaUpdateForm
from .models import ConfiguracionSistema


class ConfiguracionListView(LoginRequiredMixin, ListView):
    model = ConfiguracionSistema
    template_name = "configuracion/list.html"
    context_object_name = "configuraciones"
    paginate_by = 30

    def get_queryset(self):
        qs = ConfiguracionSistema.objects.order_by("grupo", "clave")
        q = (self.request.GET.get("q") or "").strip()
        grupo = (self.request.GET.get("grupo") or "").strip()
        if q:
            qs = qs.filter(Q(clave__icontains=q) | Q(descripcion__icontains=q))
        if grupo:
            qs = qs.filter(grupo__icontains=grupo)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Configuración del Sistema"
        ctx["q"] = self.request.GET.get("q", "")
        ctx["grupo_actual"] = self.request.GET.get("grupo", "")
        ctx["grupos"] = (
            ConfiguracionSistema.objects.exclude(grupo="")
            .values_list("grupo", flat=True)
            .distinct()
            .order_by("grupo")
        )
        return ctx


class ConfiguracionCreateView(LoginRequiredMixin, CreateView):
    model = ConfiguracionSistema
    form_class = ConfiguracionSistemaCreateForm
    template_name = "configuracion/form.html"
    success_url = reverse_lazy("configuracion:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva Configuración"
        ctx["accion"] = "Crear"
        return ctx

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Configuración «{self.object.clave}» creada.")
        return response


class ConfiguracionUpdateView(LoginRequiredMixin, UpdateView):
    model = ConfiguracionSistema
    form_class = ConfiguracionSistemaUpdateForm
    template_name = "configuracion/form.html"
    success_url = reverse_lazy("configuracion:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.editable:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Esta configuración no es editable.")
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Editar — {self.object.clave}"
        ctx["accion"] = "Guardar"
        return ctx

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Configuración «{self.object.clave}» actualizada.")
        return response
