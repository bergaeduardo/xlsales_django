# App `compartidos`

> **US #954 — compartidos baseline completo** · commit `aa96f25`

## Visión general

`compartidos` es el puente de autenticación entre el sistema legacy (SQL Server / `xlsales`) y Django (PostgreSQL). Expone:

- `Usuarios` — espejo de la tabla `Usuarios` de SQL Server, de solo lectura. Django la usa para autenticar y mapear roles, pero **nunca la modifica**.
- `RolArreglos` / `RolCads` — espejos de las tablas de roles legacy, de solo lectura.
- `PerfilUsuario` — modelo nuevo en PostgreSQL que vincula un `auth.User` Django con el UUID del usuario legacy.
- 13 grupos namespaced (`arreglos_*` / `cads_*`) creados por migración, que representan los permisos de módulo en Django.

El enrutamiento entre bases lo gestiona `XlsalesRouter` en [`core/db_router.py`](../core/db_router.py).

---

## Modelo `Usuarios` (legacy, `managed=False`)

**Fuente:** tabla `Usuarios` en la base de datos `xlsales` (SQL Server).  
**Ruta:** [`compartidos/models.py`](../../compartidos/models.py)

### Por qué `managed=False`

Con `managed=False` Django **no genera DDL** para esta tabla (ni `CREATE`, ni `ALTER`, ni `DROP`). La migración `0001` la registra en el estado interno del ORM (state-only) para que el sistema de tipos funcione, pero `sqlmigrate` produce un no-op. La tabla ya existe en SQL Server y le pertenece al sistema legacy.

### Mapeo de campos

| Campo Django         | Columna SQL Server  | Tipo         | Notas                              |
|----------------------|---------------------|--------------|------------------------------------|
| `id`                 | `id`                | UUID (PK)    | PK del registro legacy             |
| `alias`              | `alias`             | CharField    | Campo usado para login             |
| `nombre`             | `nombre`            | CharField?   |                                    |
| `apellido`           | `apellido`          | CharField?   |                                    |
| `email`              | `email`             | EmailField?  |                                    |
| `activo`             | `activo`            | Boolean      |                                    |
| `eliminado`          | `Eliminado`         | Boolean      | Nótese la mayúscula en SS          |
| `id_rol`             | `idRol`             | UUID?        |                                    |
| `id_rol_ar`          | `idRol_ar`          | UUID?        | FK conceptual a `RolArreglos`      |
| `id_rol_cads`        | `idrolcads`         | UUID?        | FK conceptual a `RolCads` (minúscula en SS) |
| `cod_empleado_tango` | `CodEmpleadoTango`  | CharField?   |                                    |

`id_rol_ar` e `id_rol_cads` son `uniqueidentifier` en SQL Server, mapeados como `UUIDField` en Django.

### Qué NO hacer

- **No renombres campos sin `db_column`.** El nombre Python y el nombre de columna SQL Server difieren; sin `db_column` explícito, Django usaría el nombre Python y rompería todas las consultas.
- **No agregues `TimeStampedModel`.** `Usuarios` es managed=False; cualquier campo de auditoría que agregues al modelo Django no existe en SQL Server y causará errores de columna.
- **No ejecutes `ALTER TABLE` desde Django** sobre esta tabla. Si la tabla legacy cambia, el cambio viene de SQL Server; Django solo necesita actualizar el modelo.

---

## Modelo `PerfilUsuario` (nuevo, `managed=True`)

**Base de datos:** `default` (PostgreSQL).  
**Ruta:** [`compartidos/models.py`](../../compartidos/models.py)  
**Migración:** [`compartidos/migrations/0001_initial.py`](../../compartidos/migrations/0001_initial.py)

Hereda de `TimeStampedModel` ([`core/models.py`](../../core/models.py)), que aporta:

| Campo        | Tipo          | Notas                                          |
|--------------|---------------|------------------------------------------------|
| `created_at` | DateTimeField | `auto_now_add=True`                            |
| `updated_at` | DateTimeField | `auto_now=True`                                |
| `created_by` | FK → User     | `db_constraint=False` (cross-DB)               |
| `updated_by` | FK → User     | `db_constraint=False` (cross-DB)               |

Campos propios:

| Campo               | Tipo                    | Restricción      | Descripción                                      |
|---------------------|-------------------------|------------------|--------------------------------------------------|
| `user`              | OneToOne → `auth.User`  | CASCADE          | Vincula al usuario Django                        |
| `usuario_legacy_id` | UUIDField               | unique, nullable | UUID del registro en `Usuarios` (SQL Server)     |

### `usuario_legacy_id`: sin FK enforced

No hay `ForeignKey` real hacia `Usuarios` porque están en bases distintas. La integridad es responsabilidad del código: al crear o actualizar un `PerfilUsuario`, debe verificarse que el UUID corresponda a un `Usuarios` existente en SQL Server.

### Patrón `CrossDbUserFkModelMixin`

`TimeStampedModel` ya incorpora `_exclude_cross_db_user_fks` en su `full_clean()`, por lo que `PerfilUsuario` hereda automáticamente el comportamiento correcto: al validar, Django no intenta cruzar la frontera de BD para verificar las FKs a `auth.User`.

Si un modelo en SQL Server **no hereda `TimeStampedModel`** pero tiene FK a `User`, debe mezclar `CrossDbUserFkModelMixin` explícitamente. Ver [`core/models.py`](../../core/models.py).

---

## Diagrama

```
PostgreSQL (default)             SQL Server (xlsales)
─────────────────────────────    ─────────────────────────────
auth.User (id: int)              Usuarios (id: UUID)
    │                                │
    │ OneToOne (CASCADE)             │
    ▼                                │
PerfilUsuario                        │
    ├── user_id → auth.User.id       │
    ├── usuario_legacy_id (UUID) ────┘  (conceptual, sin FK BD)
    ├── created_at / updated_at
    ├── created_by → auth.User (db_constraint=False)
    └── updated_by → auth.User (db_constraint=False)
```

---

## Enrutamiento de BD

`XlsalesRouter` ([`core/db_router.py`](../../core/db_router.py)) aplica la regla:

- `managed=False` en app `compartidos` → lectura/escritura en `xlsales` (SQL Server).
- `managed=True` en app `compartidos` → `None` (usa `default`, PostgreSQL).
- Migraciones de la app → solo corren en `default`.

---

## Modelos de roles legacy (`managed=False`)

**Ruta:** [`compartidos/models_roles.py`](../../compartidos/models_roles.py)

Ambos modelos viven en SQL Server (`xlsales`) y son de solo lectura. `XlsalesRouter` los enruta igual que `Usuarios`. Las migraciones state-only no generan DDL.

| Modelo        | Tabla SS            | PK                   | Campo de texto  | Extra             |
|---------------|---------------------|----------------------|-----------------|-------------------|
| `RolArreglos` | `ar_UsuariosRoles`  | `id` (UUID)          | `rol`           |                   |
| `RolCads`     | `Rol_Cads`          | `IdRol_Cads` (UUID)  | `Descripcion`   | `activo` (Bool)   |

`RolCads` tiene `activo`; el comando `migrar_usuarios` solo considera roles con `activo=True`.

**Por qué se registran en `apps.py.ready()`:** como `models_roles.py` es un módulo separado, Django no lo auto-descubría. Sin el import en `ready()`, `makemigrations --check` detectaba estado inconsistente.

```python
# compartidos/apps.py
def ready(self):
    from . import models_roles  # noqa: F401
```

---

## Grupos namespaced

13 grupos creados por la migración `0002` en PostgreSQL (`default`):

**Módulo Arreglos:**

| Grupo                 | Rol                        |
|-----------------------|----------------------------|
| `arreglos_admin`      | Administrador              |
| `arreglos_operador`   | Operador genérico          |
| `arreglos_consultor`  | Solo lectura               |
| `arreglos_deposito`   | Operador de depósito       |
| `arreglos_emisor`     | Emisor de comprobantes     |
| `arreglos_fabrica`    | Operador de fábrica        |

**Módulo CADS:**

| Grupo                        | Rol                       |
|------------------------------|---------------------------|
| `cads_admin`                 | Administrador             |
| `cads_operador`              | Operador genérico         |
| `cads_contabilidad`          | Contabilidad              |
| `cads_deposito`              | Operador de depósito      |
| `cads_emisor`                | Emisor                    |
| `cads_emisor_mayorista`      | Emisor mayorista          |
| `cads_responsable_comercial` | Responsable comercial     |

Son los únicos grupos **gestionados por el sistema**; cualquier otro grupo asignado a un usuario se preserva sin tocar.

---

## Helper `sync_grupos` ([`compartidos/roles.py`](../../compartidos/roles.py))

```python
sync_grupos(user, grupo_ar, grupo_cads)
```

Reemplaza los grupos gestionados (`arreglos_*/cads_*`) del usuario por los nuevos valores, **preservando cualquier otro grupo** que el usuario tenga asignado.

- `grupo_ar` / `grupo_cads`: nombre de grupo o `None` (sin asignación).
- Idempotente: llamar dos veces con los mismos argumentos produce el mismo resultado.

`GRUPOS_GESTIONADOS` incluye los 13 grupos de ambos módulos — constante exportada para uso en tests y admin.

---

## Helpers de permisos ([`compartidos/permissions.py`](../../compartidos/permissions.py))

Todos validan `user.is_active` antes de consultar grupos. Convención: `is_<módulo>_<rol>(user)`.

**Arreglos:**

| Función                       | Grupo chequeado         |
|-------------------------------|-------------------------|
| `is_arreglos_admin(user)`     | `arreglos_admin`        |
| `is_arreglos_operador(user)`  | `arreglos_operador`     |
| `is_arreglos_consultor(user)` | `arreglos_consultor`    |
| `is_arreglos_deposito(user)`  | `arreglos_deposito`     |
| `is_arreglos_emisor(user)`    | `arreglos_emisor`       |
| `is_arreglos_fabrica(user)`   | `arreglos_fabrica`      |

**CADS:**

| Función                              | Grupo chequeado              |
|--------------------------------------|------------------------------|
| `is_cads_admin(user)`                | `cads_admin`                 |
| `is_cads_operador(user)`             | `cads_operador`              |
| `is_cads_contabilidad(user)`         | `cads_contabilidad`          |
| `is_cads_deposito(user)`             | `cads_deposito`              |
| `is_cads_emisor(user)`               | `cads_emisor`                |
| `is_cads_emisor_mayorista(user)`     | `cads_emisor_mayorista`      |
| `is_cads_responsable_comercial(user)`| `cads_responsable_comercial` |

**Acceso por módulo:**

| Función                              | Retorna `True` si...                                 |
|--------------------------------------|------------------------------------------------------|
| `has_module_access(user, "arreglos")`| pertenece a cualquier grupo `arreglos_*`             |
| `has_module_access(user, "cads")`    | pertenece a cualquier grupo `cads_*`                 |

Uso típico en vistas:
```python
from compartidos.permissions import is_arreglos_admin
if not is_arreglos_admin(request.user):
    raise PermissionDenied
```

---

## Comando `migrar_usuarios`

**Ruta:** [`compartidos/management/commands/migrar_usuarios.py`](../../compartidos/management/commands/migrar_usuarios.py)

Migra usuarios desde SQL Server (`xlsales`) a Django. **Idempotente** — puede correr múltiples veces sin duplicar datos.

```bash
python manage.py migrar_usuarios [--dry-run] [--only-user ALIAS] [--batch-size N]
```

| Flag            | Default | Descripción                                              |
|-----------------|---------|----------------------------------------------------------|
| `--dry-run`     | off     | Simula sin commitear; muestra matriz de roles primero    |
| `--only-user`   | (todos) | Migra únicamente el usuario con ese alias                |
| `--batch-size`  | 100     | Usuarios por lote (OFFSET/FETCH en SQL Server)           |

### Comportamiento

1. En `--dry-run`: muestra primero los roles DISTINCT de cada tabla con su mapeo al grupo Django, luego simula sin commitear.
2. Lee `Usuarios` con `order_by("id")` — requerido para que `OFFSET/FETCH` de SQL Server sea determinístico entre lotes.
3. Solo procesa usuarios `activo=True, eliminado=False`.
4. Por cada usuario: `update_or_create` de `auth.User` → `set_unusable_password()` (no se portan hashes legacy) → `update_or_create` de `PerfilUsuario` → `sync_grupos()`.
5. Cada usuario se procesa en `transaction.atomic()` — un error no aborta el lote completo.
6. Contador `sin_rol` cuando el usuario no mapea a ningún grupo (se crea igualmente, sin grupos gestionados).

### Mapeo de roles

El mapeo es por nombre normalizado (strip + lowercase), con diccionarios `_ROL_AR_MAP` / `_ROL_CADS_MAP`:

**Arreglos (`ar_UsuariosRoles.rol`):**

| Valor en SS                          | Grupo Django          |
|--------------------------------------|-----------------------|
| `admin`, `administrador`, `supervisor` | `arreglos_admin`    |
| `operador`, `user`, `vendedor`       | `arreglos_operador`   |
| `consultor`                          | `arreglos_consultor`  |
| `deposito`                           | `arreglos_deposito`   |
| `emisor`                             | `arreglos_emisor`     |
| `fabrica`                            | `arreglos_fabrica`    |
| cualquier otro valor                 | `sin_rol`             |

**CADS (`Rol_Cads.Descripcion`, solo `activo=True`):**

| Valor en SS                          | Grupo Django                  |
|--------------------------------------|-------------------------------|
| `admin`, `administrador`, `supervisor` | `cads_admin`                |
| `operador`, `user`, `vendedor`       | `cads_operador`               |
| `contabilidad`                       | `cads_contabilidad`           |
| `deposito`                           | `cads_deposito`               |
| `emisor`                             | `cads_emisor`                 |
| `emisor mayorista`                   | `cads_emisor_mayorista`       |
| `responsable comercial`              | `cads_responsable_comercial`  |
| cualquier otro valor                 | `sin_rol`                     |

### Ejemplo salida `--dry-run`

```
DRY-RUN activo — no se commitearán cambios.

=== Arreglos (ar_UsuariosRoles.rol) ===
  'Administrador'                     →  arreglos_admin
  'Consultor'                         →  SIN MAPEO
Resumen: 1 mapeados, 1 sin mapeo

=== CADS (Rol_Cads.Descripcion) ===
  'Administrador'                     →  cads_admin
  'Emisor'                            →  cads_emisor
Resumen: 2 mapeados, 0 sin mapeo
```

### Resumen final

```
==================================================
created=42  updated=18  sin_rol=3  errors=0
```

---

> **⚠️ Acción pendiente pre-cutover**
>
> Antes de ejecutar la migración real contra producción:
>
> 1. Correr `python manage.py migrar_usuarios --dry-run` contra la BD de producción.
> 2. Capturar los valores reales de `ar_UsuariosRoles.rol` y `Rol_Cads.Descripcion` que aparezcan como `SIN MAPEO`.
> 3. Cerrar la matriz nombre_rol → grupo con Eduardo.
> 4. Ajustar `_ROL_AR_MAP` / `_ROL_CADS_MAP` en el comando, o migrar a tabla de mapeo explícita.
>
> **No correr sin este paso.** Los roles `SIN MAPEO` resultan en usuarios creados sin acceso a ningún módulo.

---

## Admin UX ([`compartidos/admin.py`](../../compartidos/admin.py))

`UserAdmin` extiende el admin estándar de Django con:

- **`UserRolForm`**: agrega campos desplegables `rol_arreglos` y `rol_cads` al formulario de usuario. Al guardar, llama `sync_grupos()` desde `save_model()`.
- **`PerfilUsuarioInline`**: muestra `usuario_legacy_id` inline en el usuario. Usa `fk_name="user"` para resolver el conflicto `admin.E202` que surge porque `TimeStampedModel` tiene múltiples FKs a `User` además del `OneToOneField` de `PerfilUsuario`.

---

## Migraciones (resumen)

| Nro  | Descripción                                         | DDL real |
|------|-----------------------------------------------------|----------|
| 0001 | `PerfilUsuario` (PG) + `Usuarios` state-only (SS)  | Sí (PerfilUsuario) / No (Usuarios) |
| 0002 | Crea los 13 grupos namespaced en `auth_group` (PG) | Sí (via `RunPython`) |
| 0003 | `RolArreglos` + `RolCads` state-only (SS)           | No       |

---

## Tests

**48 tests · cobertura 86%** · [`compartidos/tests/`](../../compartidos/tests/)

| Archivo                         | Cobertura del módulo   |
|---------------------------------|------------------------|
| `test_models.py`                | `models.py` 100%       |
| `test_permissions_roles.py`     | `permissions.py` 100%, `roles.py` 100% |
| `test_migrar_usuarios.py`       | `management/commands/migrar_usuarios.py` 75% |
| _(compartidos total)_           | 86%                    |
