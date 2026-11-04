"""
Tests US #954 — compartidos: Usuarios (managed=False) + PerfilUsuario (managed=True).

Estructura:
  1. Tests de meta del modelo Usuarios   — sin acceso a BD.
  2. Tests de PerfilUsuario              — @pytest.mark.django_db, DB default.
  3. Smoke de migraciones               — makemigrations --check + sqlmigrate.
"""
import io
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError

from compartidos.models import PerfilUsuario, Usuarios

User = get_user_model()


# =============================================================================
# 1. Tests de estructura del modelo Usuarios (sin acceso a BD)
# =============================================================================


def test_usuarios_managed_false():
    assert Usuarios._meta.managed is False


def test_usuarios_db_table():
    assert Usuarios._meta.db_table == "Usuarios"


def test_usuarios_app_label():
    assert Usuarios._meta.app_label == "compartidos"


def test_usuarios_pk_is_id_uuid():
    pk = Usuarios._meta.pk
    assert pk.name == "id"
    assert pk.__class__.__name__ == "UUIDField"
    assert pk.db_column == "id"


def test_usuarios_db_columns_match_ss():
    expected = {
        "alias": "alias",
        "nombre": "nombre",
        "apellido": "apellido",
        "email": "email",
        "activo": "activo",
        "eliminado": "Eliminado",
        "id_rol": "idRol",
        "id_rol_ar": "idRol_ar",
        "id_rol_cads": "idrolcads",
        "cod_empleado_tango": "CodEmpleadoTango",
    }
    fields = {f.name: f for f in Usuarios._meta.get_fields() if hasattr(f, "db_column")}
    for field_name, expected_col in expected.items():
        assert field_name in fields, f"Campo '{field_name}' no encontrado en Usuarios"
        actual_col = fields[field_name].db_column
        assert actual_col == expected_col, (
            f"Usuarios.{field_name}: db_column esperado '{expected_col}', "
            f"encontrado '{actual_col}'"
        )


def test_usuarios_roles_are_uuid():
    fields = {f.name: f for f in Usuarios._meta.get_fields() if hasattr(f, "db_column")}
    for fname in ("id_rol_ar", "id_rol_cads"):
        assert fields[fname].__class__.__name__ == "UUIDField", (
            f"Usuarios.{fname} debe ser UUIDField"
        )


def test_usuarios_str():
    u = Usuarios(
        id=uuid.uuid4(),
        alias="jdoe",
        nombre="John",
        apellido="Doe",
        activo=True,
        eliminado=False,
    )
    result = str(u)
    assert isinstance(result, str)
    assert len(result) > 0


# =============================================================================
# 2. Tests de PerfilUsuario (usa BD default)
# =============================================================================


@pytest.mark.django_db
def test_perfil_crea_ok():
    user = User.objects.create_user(username="testuser1", password="pass")
    legacy_id = uuid.uuid4()
    perfil = PerfilUsuario.objects.create(user=user, usuario_legacy_id=legacy_id)
    perfil.refresh_from_db()
    assert perfil.pk is not None
    assert perfil.usuario_legacy_id == legacy_id


@pytest.mark.django_db
def test_perfil_usuario_legacy_id_unique():
    legacy_id = uuid.uuid4()
    user1 = User.objects.create_user(username="uniqueuser1", password="pass")
    user2 = User.objects.create_user(username="uniqueuser2", password="pass")
    PerfilUsuario.objects.create(user=user1, usuario_legacy_id=legacy_id)
    with pytest.raises(IntegrityError):
        PerfilUsuario.objects.create(user=user2, usuario_legacy_id=legacy_id)


@pytest.mark.django_db
def test_perfil_usuario_legacy_id_null_ok():
    user1 = User.objects.create_user(username="nulluser1", password="pass")
    user2 = User.objects.create_user(username="nulluser2", password="pass")
    p1 = PerfilUsuario.objects.create(user=user1, usuario_legacy_id=None)
    p2 = PerfilUsuario.objects.create(user=user2, usuario_legacy_id=None)
    assert p1.pk != p2.pk


@pytest.mark.django_db
def test_perfil_timestamped():
    user = User.objects.create_user(username="tsuser", password="pass")
    perfil = PerfilUsuario.objects.create(user=user)
    assert perfil.created_at is not None
    assert perfil.updated_at is not None


@pytest.mark.django_db
def test_perfil_related_name():
    user = User.objects.create_user(username="reluser", password="pass")
    perfil = PerfilUsuario.objects.create(user=user)
    assert user.perfil == perfil


@pytest.mark.django_db
def test_perfil_cascade_delete():
    user = User.objects.create_user(username="cascadeuser", password="pass")
    perfil_pk = PerfilUsuario.objects.create(user=user).pk
    user.delete()
    assert not PerfilUsuario.objects.filter(pk=perfil_pk).exists()


@pytest.mark.django_db
def test_perfil_str():
    user = User.objects.create_user(username="struser", password="pass")
    perfil = PerfilUsuario.objects.create(user=user)
    assert str(perfil) == f"Perfil de {user}"


@pytest.mark.django_db
def test_perfil_update_legacy_id():
    user = User.objects.create_user(username="updateuser", password="pass")
    perfil = PerfilUsuario.objects.create(user=user, usuario_legacy_id=None)
    new_id = uuid.uuid4()
    perfil.usuario_legacy_id = new_id
    perfil.save()
    perfil.refresh_from_db()
    assert perfil.usuario_legacy_id == new_id


# =============================================================================
# 3. Smoke de migraciones
# =============================================================================


@pytest.mark.django_db(databases=["default", "xlsales", "tango"])
def test_migrations_consistent():
    """makemigrations compartidos --check: no debe detectar cambios pendientes en esta app."""
    call_command("makemigrations", "compartidos", "--check", "--dry-run", verbosity=0)


@pytest.mark.django_db(transaction=True)
def test_sqlmigrate_usuarios_is_noop():
    """sqlmigrate compartidos 0001 no debe contener CREATE TABLE "Usuarios".

    transaction=True evita el wrapping en savepoint de SQLite, que bloquea
    el schema editor que sqlmigrate necesita internamente.
    """
    buf = io.StringIO()
    call_command("sqlmigrate", "compartidos", "0001", stdout=buf)
    sql_output = buf.getvalue()
    assert 'CREATE TABLE "Usuarios"' not in sql_output, (
        "La migración 0001 no debería crear la tabla Usuarios (managed=False).\n"
        f"SQL generado:\n{sql_output}"
    )
