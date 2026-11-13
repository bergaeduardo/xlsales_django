"""
Helpers de autorización por grupo namespaced.

Grupos Arreglos:
  arreglos_admin              — administrador del módulo Arreglos
  arreglos_operador           — operador genérico
  arreglos_consultor          — consultor (solo lectura)
  arreglos_deposito           — operador de depósito
  arreglos_emisor             — emisor de comprobantes
  arreglos_fabrica            — operador de fábrica

Grupos CADS:
  cads_admin                  — administrador del módulo CADS
  cads_operador               — operador genérico
  cads_contabilidad           — contabilidad
  cads_deposito               — operador de depósito
  cads_emisor                 — emisor
  cads_emisor_mayorista       — emisor mayorista
  cads_responsable_comercial  — responsable comercial

Uso típico en views:
    from compartidos.permissions import is_arreglos_admin
    if not is_arreglos_admin(request.user):
        raise PermissionDenied
"""

_ARREGLOS_GROUPS = {
    "arreglos_admin", "arreglos_operador",
    "arreglos_consultor", "arreglos_deposito", "arreglos_emisor", "arreglos_fabrica",
}
_CADS_GROUPS = {
    "cads_admin", "cads_operador",
    "cads_contabilidad", "cads_deposito", "cads_emisor",
    "cads_emisor_mayorista", "cads_responsable_comercial",
}


def _user_in_group(user, group_name: str) -> bool:
    if not user or not user.is_active:
        return False
    return user.groups.filter(name=group_name).exists()


# --- Arreglos ---

def is_arreglos_admin(user) -> bool:
    return _user_in_group(user, "arreglos_admin")


def is_arreglos_operador(user) -> bool:
    return _user_in_group(user, "arreglos_operador")


def is_arreglos_consultor(user) -> bool:
    return _user_in_group(user, "arreglos_consultor")


def is_arreglos_deposito(user) -> bool:
    return _user_in_group(user, "arreglos_deposito")


def is_arreglos_emisor(user) -> bool:
    return _user_in_group(user, "arreglos_emisor")


def is_arreglos_fabrica(user) -> bool:
    return _user_in_group(user, "arreglos_fabrica")


# --- CADS ---

def is_cads_admin(user) -> bool:
    return _user_in_group(user, "cads_admin")


def is_cads_operador(user) -> bool:
    return _user_in_group(user, "cads_operador")


def is_cads_contabilidad(user) -> bool:
    return _user_in_group(user, "cads_contabilidad")


def is_cads_deposito(user) -> bool:
    return _user_in_group(user, "cads_deposito")


def is_cads_emisor(user) -> bool:
    return _user_in_group(user, "cads_emisor")


def is_cads_emisor_mayorista(user) -> bool:
    return _user_in_group(user, "cads_emisor_mayorista")


def is_cads_responsable_comercial(user) -> bool:
    return _user_in_group(user, "cads_responsable_comercial")


# --- Acceso por módulo ---

def has_module_access(user, modulo: str) -> bool:
    """
    Devuelve True si el usuario pertenece a cualquier grupo del módulo.

    modulo: "arreglos" | "cads"
    """
    if not user or not user.is_active:
        return False
    if modulo == "arreglos":
        return user.groups.filter(name__in=_ARREGLOS_GROUPS).exists()
    if modulo == "cads":
        return user.groups.filter(name__in=_CADS_GROUPS).exists()
    return False
