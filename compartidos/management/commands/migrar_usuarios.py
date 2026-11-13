"""
Comando idempotente para migrar usuarios desde SQL Server (xlsales) a Django.

Uso:
    python manage.py migrar_usuarios
    python manage.py migrar_usuarios --dry-run
    python manage.py migrar_usuarios --only-user jperez
    python manage.py migrar_usuarios --batch-size 50

Mapeo de nombres de rol a grupo Django:
  Arreglos (tabla ar_UsuariosRoles, campo 'rol'):
    admin|administrador|supervisor  → arreglos_admin
    operador|user|vendedor          → arreglos_operador

  CADS (tabla Rol_Cads, campo 'Descripcion'):
    admin|administrador|supervisor  → cads_admin
    operador|user|vendedor          → cads_operador

Si el nombre no mapea, el usuario se crea/actualiza sin grupo asignado
(se contabiliza en 'sin_rol'). Ver --dry-run para inspeccionar la matriz
completa antes de correr contra producción.
Los hashes de contraseña legacy NO se portan; se llama set_unusable_password().
"""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from compartidos.models import PerfilUsuario, Usuarios
from compartidos.models_roles import RolArreglos, RolCads
from compartidos.roles import sync_grupos

logger = logging.getLogger(__name__)

User = get_user_model()

# Mapeo exacto nombre_rol (normalizado) → grupo Django, por módulo.
_ROL_AR_MAP = {
    "admin": "arreglos_admin",
    "administrador": "arreglos_admin",
    "supervisor": "arreglos_admin",
    "operador": "arreglos_operador",
    "user": "arreglos_operador",
    "vendedor": "arreglos_operador",
    "consultor": "arreglos_consultor",
    "deposito": "arreglos_deposito",
    "emisor": "arreglos_emisor",
    "fabrica": "arreglos_fabrica",
}

_ROL_CADS_MAP = {
    "admin": "cads_admin",
    "administrador": "cads_admin",
    "supervisor": "cads_admin",
    "operador": "cads_operador",
    "user": "cads_operador",
    "vendedor": "cads_operador",
    "contabilidad": "cads_contabilidad",
    "deposito": "cads_deposito",
    "emisor": "cads_emisor",
    "emisor mayorista": "cads_emisor_mayorista",
    "responsable comercial": "cads_responsable_comercial",
}


def _normalizar_a_grupo(nombre_rol: str, prefijo: str) -> str | None:
    """
    Convierte el nombre del rol (string libre de SS) en el nombre del grupo Django.
    prefijo: "arreglos" | "cads"
    Retorna None si no mapea.
    """
    clave = nombre_rol.strip().lower()
    mapa = _ROL_AR_MAP if prefijo == "arreglos" else _ROL_CADS_MAP
    return mapa.get(clave)


def _build_rol_ar_map() -> dict:
    """UUID (idRol_ar) → nombre grupo Django para Arreglos."""
    resultado = {}
    for rol in RolArreglos.objects.all():
        grupo = _normalizar_a_grupo(rol.rol, "arreglos")
        if grupo:
            resultado[rol.id] = grupo
        else:
            logger.warning("RolArreglos '%s' (id=%s) no mapea a ningún grupo.", rol.rol, rol.id)
    return resultado


def _build_rol_cads_map() -> dict:
    """UUID (idrolcads) → nombre grupo Django para CADS."""
    resultado = {}
    for rol in RolCads.objects.filter(activo=True):
        nombre = rol.descripcion or ""
        grupo = _normalizar_a_grupo(nombre, "cads")
        if grupo:
            resultado[rol.id_rol_cads] = grupo
        else:
            logger.warning("RolCads '%s' (id=%s) no mapea a ningún grupo.", nombre, rol.id_rol_cads)
    return resultado


class Command(BaseCommand):
    help = "Migra usuarios desde SQL Server (xlsales) a Django. Idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la migración sin commitear cambios.",
        )
        parser.add_argument(
            "--only-user",
            metavar="ALIAS",
            help="Migra únicamente el usuario con ese alias.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            metavar="N",
            help="Cantidad de usuarios por lote (default: 100).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_user = options["only_user"]
        batch_size = options["batch_size"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activo — no se commitearán cambios."))
            self._listar_roles_dry_run()

        # Cachear mapeos de roles al inicio (evita N+1 en el loop).
        rol_ar_map = _build_rol_ar_map()
        rol_cads_map = _build_rol_cads_map()

        # F2: order_by estable para OFFSET/FETCH en SQL Server (sin orden determinístico
        # el slicing puede saltear o duplicar filas entre lotes).
        qs = Usuarios.objects.using("xlsales").filter(activo=True, eliminado=False).order_by("id")
        if only_user:
            qs = qs.filter(alias=only_user)

        contadores = {"created": 0, "updated": 0, "sin_rol": 0, "errors": 0}
        errores_detalle = []

        offset = 0
        while True:
            lote = list(qs[offset : offset + batch_size])
            if not lote:
                break
            offset += batch_size

            for legacy in lote:
                try:
                    self._migrar_usuario(legacy, rol_ar_map, rol_cads_map, dry_run, contadores)
                except Exception as exc:
                    contadores["errors"] += 1
                    msg = f"Error en alias={legacy.alias}: {exc}"
                    errores_detalle.append(msg)
                    logger.error(msg, exc_info=True)

        self._report(contadores, errores_detalle)

    def _listar_roles_dry_run(self) -> None:
        """Muestra los roles DISTINCT de cada tabla y su mapeo al grupo Django."""
        self.stdout.write("\n=== Arreglos (ar_UsuariosRoles.rol) ===")
        roles_ar = (
            RolArreglos.objects.values_list("rol", flat=True).distinct().order_by("rol")
        )
        mapeados = sin_mapeo = 0
        for rol in roles_ar:
            grupo = _normalizar_a_grupo(rol or "", "arreglos")
            if grupo:
                self.stdout.write(f"  {repr(rol):<35} →  {grupo}")
                mapeados += 1
            else:
                self.stdout.write(f"  {repr(rol):<35} →  SIN MAPEO")
                sin_mapeo += 1
        self.stdout.write(f"Resumen: {mapeados} mapeados, {sin_mapeo} sin mapeo")

        self.stdout.write("\n=== CADS (Rol_Cads.Descripcion) ===")
        roles_cads = (
            RolCads.objects.values_list("descripcion", flat=True).distinct().order_by("descripcion")
        )
        mapeados = sin_mapeo = 0
        for desc in roles_cads:
            grupo = _normalizar_a_grupo(desc or "", "cads")
            if grupo:
                self.stdout.write(f"  {repr(desc):<35} →  {grupo}")
                mapeados += 1
            else:
                self.stdout.write(f"  {repr(desc):<35} →  SIN MAPEO")
                sin_mapeo += 1
        self.stdout.write(f"Resumen: {mapeados} mapeados, {sin_mapeo} sin mapeo\n")

    def _migrar_usuario(self, legacy, rol_ar_map, rol_cads_map, dry_run, contadores):
        username = legacy.alias
        defaults = {
            "first_name": (legacy.nombre or "")[:150],
            "last_name": (legacy.apellido or "")[:150],
            "email": legacy.email or "",
            "is_active": True,
        }

        grupo_ar = rol_ar_map.get(legacy.id_rol_ar)
        grupo_cads = rol_cads_map.get(legacy.id_rol_cads)

        if dry_run:
            existe = User.objects.filter(username=username).exists()
            accion = "updated" if existe else "created"
            contadores[accion] += 1
            if not grupo_ar and not grupo_cads:
                contadores["sin_rol"] += 1
            self.stdout.write(f"  [{accion}] {username}")
            return

        with transaction.atomic():
            user, created = User.objects.update_or_create(
                username=username, defaults=defaults
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])

            PerfilUsuario.objects.update_or_create(
                user=user,
                defaults={"usuario_legacy_id": legacy.id},
            )

            if not grupo_ar and not grupo_cads:
                contadores["sin_rol"] += 1
            sync_grupos(user, grupo_ar, grupo_cads)

            if created:
                contadores["created"] += 1
                self.stdout.write(f"  [created] {username}")
            else:
                contadores["updated"] += 1
                self.stdout.write(f"  [updated] {username}")

    def _report(self, contadores, errores_detalle):
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"created={contadores['created']}  "
                f"updated={contadores['updated']}  "
                f"sin_rol={contadores['sin_rol']}  "
                f"errors={contadores['errors']}"
            )
        )
        if errores_detalle:
            self.stdout.write(self.style.ERROR("\nErrores:"))
            for e in errores_detalle:
                self.stdout.write(f"  {e}")
