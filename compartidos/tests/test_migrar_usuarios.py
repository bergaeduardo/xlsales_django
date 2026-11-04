"""
Tests US #955 iter 2 — migrar_usuarios.

Cubre:
  F2 - order_by estable antes del batcheo (OFFSET/FETCH en SQL Server)
  F3 - contador sin_rol se incrementa cuando ningún grupo mapea
  HITL - --dry-run lista roles DISTINCT marcando SIN MAPEO
"""
import io
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command


# ---------------------------------------------------------------------------
# Helpers para armar mocks de managers de forma legible
# ---------------------------------------------------------------------------

def _make_usuarios_mock(orden_qs=None):
    """
    Devuelve (mock_Usuarios, mock_filter_result, mock_ordered_qs).
    mock_filter_result.order_by.return_value == mock_ordered_qs
    mock_ordered_qs[x:y] devuelve [] (lote vacío → loop termina al primer intento).
    """
    mock_ordered = MagicMock()
    mock_ordered.__getitem__ = MagicMock(return_value=[])

    mock_filter = MagicMock()
    mock_filter.order_by.return_value = mock_ordered
    mock_filter.filter.return_value = mock_filter  # para --only-user

    mock_Usuarios = MagicMock()
    mock_Usuarios.objects.using.return_value.filter.return_value = mock_filter
    return mock_Usuarios, mock_filter, mock_ordered


def _make_roles_mock(roles_ar=None, roles_cads=None):
    """
    Devuelve (mock_RolArreglos, mock_RolCads) con:
      - .objects.all()          → [] (vacío para _build_rol_*_map)
      - .objects.filter()       → [] (vacío para _build_rol_cads_map)
      - .objects.values_list… → lista de nombres para _listar_roles_dry_run
    """
    roles_ar = roles_ar or []
    roles_cads = roles_cads or []

    mock_RolAr = MagicMock()
    mock_RolAr.objects.all.return_value = []
    # values_list("rol", flat=True).distinct().order_by("rol")
    mock_RolAr.objects.values_list.return_value.distinct.return_value.order_by.return_value = roles_ar

    mock_RolCads = MagicMock()
    mock_RolCads.objects.filter.return_value = []  # _build_rol_cads_map
    # values_list("descripcion", flat=True).distinct().order_by("descripcion")
    mock_RolCads.objects.values_list.return_value.distinct.return_value.order_by.return_value = roles_cads

    return mock_RolAr, mock_RolCads


# ---------------------------------------------------------------------------
# F2: order_by estable en el queryset de batcheo
# ---------------------------------------------------------------------------

def test_batching_tiene_order_by():
    """handle() llama .order_by('id') sobre el qs de Usuarios antes de paginar."""
    mock_Usuarios, mock_filter, _ = _make_usuarios_mock()
    mock_RolAr, mock_RolCads = _make_roles_mock()

    with (
        patch("compartidos.management.commands.migrar_usuarios.Usuarios", mock_Usuarios),
        patch("compartidos.management.commands.migrar_usuarios.RolArreglos", mock_RolAr),
        patch("compartidos.management.commands.migrar_usuarios.RolCads", mock_RolCads),
    ):
        call_command("migrar_usuarios", stdout=io.StringIO())

    mock_filter.order_by.assert_called_once_with("id")


# ---------------------------------------------------------------------------
# F3: contador sin_rol
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sin_rol_se_incrementa_en_dry_run():
    """Usuarios sin ningún grupo mapeado incrementan sin_rol en dry-run."""
    import uuid
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Legacy user con roles que NO mapean
    legacy = MagicMock()
    legacy.alias = "usuario_sin_rol"
    legacy.nombre = "Test"
    legacy.apellido = "User"
    legacy.email = "test@test.com"
    legacy.id = uuid.uuid4()
    legacy.id_rol_ar = uuid.uuid4()   # no está en ningún mapa
    legacy.id_rol_cads = uuid.uuid4()  # no está en ningún mapa

    mock_ordered = MagicMock()
    # Primer slice devuelve el legacy user, segundo devuelve [] para terminar
    mock_ordered.__getitem__ = MagicMock(side_effect=[[legacy], []])

    mock_filter = MagicMock()
    mock_filter.order_by.return_value = mock_ordered
    mock_filter.filter.return_value = mock_filter

    mock_Usuarios = MagicMock()
    mock_Usuarios.objects.using.return_value.filter.return_value = mock_filter

    mock_RolAr, mock_RolCads = _make_roles_mock()

    out = io.StringIO()
    with (
        patch("compartidos.management.commands.migrar_usuarios.Usuarios", mock_Usuarios),
        patch("compartidos.management.commands.migrar_usuarios.RolArreglos", mock_RolAr),
        patch("compartidos.management.commands.migrar_usuarios.RolCads", mock_RolCads),
    ):
        call_command("migrar_usuarios", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "sin_rol=1" in output


# ---------------------------------------------------------------------------
# HITL: --dry-run lista roles con SIN MAPEO
# ---------------------------------------------------------------------------

def test_dry_run_lista_roles_sin_mapeo():
    """--dry-run muestra sección de roles con 'SIN MAPEO' para los no mapeados."""
    roles_ar = ["Administrador", "Deposito"]      # Deposito → SIN MAPEO
    roles_cads = ["Admin", "Externo"]             # Externo → SIN MAPEO

    mock_Usuarios, _, _ = _make_usuarios_mock()
    mock_RolAr, mock_RolCads = _make_roles_mock(roles_ar=roles_ar, roles_cads=roles_cads)

    out = io.StringIO()
    with (
        patch("compartidos.management.commands.migrar_usuarios.Usuarios", mock_Usuarios),
        patch("compartidos.management.commands.migrar_usuarios.RolArreglos", mock_RolAr),
        patch("compartidos.management.commands.migrar_usuarios.RolCads", mock_RolCads),
    ):
        call_command("migrar_usuarios", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "SIN MAPEO" in output, "Debe aparecer 'SIN MAPEO' para roles no mapeados"
    assert "Deposito" in output, "Rol Arreglos no mapeado debe estar en el output"
    assert "Externo" in output, "Rol CADS no mapeado debe estar en el output"
    assert "arreglos_admin" in output, "Rol mapeado debe aparecer con su grupo"
    assert "cads_admin" in output, "Rol CADS mapeado debe aparecer con su grupo"
    assert "=== Arreglos" in output
    assert "=== CADS" in output


def test_dry_run_resumen_por_tabla():
    """--dry-run muestra línea 'Resumen: N mapeados, M sin mapeo' por tabla."""
    roles_ar = ["Administrador", "Deposito", "Externo"]    # 2 mapeados, 1 sin mapeo (Externo no mapea)
    roles_cads = []  # sin roles → 0 mapeados, 0 sin mapeo

    mock_Usuarios, _, _ = _make_usuarios_mock()
    mock_RolAr, mock_RolCads = _make_roles_mock(roles_ar=roles_ar, roles_cads=roles_cads)

    out = io.StringIO()
    with (
        patch("compartidos.management.commands.migrar_usuarios.Usuarios", mock_Usuarios),
        patch("compartidos.management.commands.migrar_usuarios.RolArreglos", mock_RolAr),
        patch("compartidos.management.commands.migrar_usuarios.RolCads", mock_RolCads),
    ):
        call_command("migrar_usuarios", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "Resumen: 2 mapeados, 1 sin mapeo" in output
    assert "Resumen: 0 mapeados, 0 sin mapeo" in output
