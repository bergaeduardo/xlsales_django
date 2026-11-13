from django.contrib.auth.models import Group

GRUPOS_GESTIONADOS = {
    "arreglos_admin", "arreglos_operador",
    "arreglos_consultor", "arreglos_deposito", "arreglos_emisor", "arreglos_fabrica",
    "cads_admin", "cads_operador",
    "cads_contabilidad", "cads_deposito", "cads_emisor",
    "cads_emisor_mayorista", "cads_responsable_comercial",
}


def sync_grupos(user, grupo_ar: str | None, grupo_cads: str | None) -> None:
    """Reemplaza grupos arreglos_*/cads_* del usuario por los nuevos."""
    actuales = set(user.groups.values_list("name", flat=True))
    mantener = actuales - GRUPOS_GESTIONADOS

    nuevos = set()
    if grupo_ar:
        nuevos.add(grupo_ar)
    if grupo_cads:
        nuevos.add(grupo_cads)

    grupos_finales = Group.objects.filter(name__in=mantener | nuevos)
    user.groups.set(grupos_finales)
