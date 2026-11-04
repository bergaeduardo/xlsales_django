"""Tests para compartidos/permissions.py y compartidos/roles.py."""
import pytest
from django.contrib.auth.models import Group

from compartidos.permissions import (
    has_module_access,
    is_arreglos_admin,
    is_arreglos_consultor,
    is_arreglos_deposito,
    is_arreglos_emisor,
    is_arreglos_fabrica,
    is_arreglos_operador,
    is_cads_admin,
    is_cads_contabilidad,
    is_cads_deposito,
    is_cads_emisor,
    is_cads_emisor_mayorista,
    is_cads_operador,
    is_cads_responsable_comercial,
)
from compartidos.roles import sync_grupos


def _create_group(name):
    group, _ = Group.objects.get_or_create(name=name)
    return group


# ---------------------------------------------------------------------------
# _user_in_group via is_* helpers
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_perms_usuario_inactivo_siempre_false(django_user_model):
    user = django_user_model.objects.create_user(username="inactivo", password="pw", is_active=False)
    group = _create_group("arreglos_admin")
    user.groups.add(group)
    assert is_arreglos_admin(user) is False


@pytest.mark.django_db
def test_perms_none_user():
    assert is_arreglos_admin(None) is False


@pytest.mark.django_db
def test_perms_arreglos_admin_verdadero(django_user_model):
    user = django_user_model.objects.create_user(username="u1", password="pw")
    user.groups.add(_create_group("arreglos_admin"))
    assert is_arreglos_admin(user) is True


@pytest.mark.django_db
def test_perms_arreglos_operador(django_user_model):
    user = django_user_model.objects.create_user(username="u2", password="pw")
    user.groups.add(_create_group("arreglos_operador"))
    assert is_arreglos_operador(user) is True
    assert is_arreglos_admin(user) is False


@pytest.mark.django_db
def test_perms_arreglos_consultor(django_user_model):
    user = django_user_model.objects.create_user(username="u3", password="pw")
    user.groups.add(_create_group("arreglos_consultor"))
    assert is_arreglos_consultor(user) is True


@pytest.mark.django_db
def test_perms_arreglos_deposito(django_user_model):
    user = django_user_model.objects.create_user(username="u4", password="pw")
    user.groups.add(_create_group("arreglos_deposito"))
    assert is_arreglos_deposito(user) is True


@pytest.mark.django_db
def test_perms_arreglos_emisor(django_user_model):
    user = django_user_model.objects.create_user(username="u5", password="pw")
    user.groups.add(_create_group("arreglos_emisor"))
    assert is_arreglos_emisor(user) is True


@pytest.mark.django_db
def test_perms_arreglos_fabrica(django_user_model):
    user = django_user_model.objects.create_user(username="u6", password="pw")
    user.groups.add(_create_group("arreglos_fabrica"))
    assert is_arreglos_fabrica(user) is True


@pytest.mark.django_db
def test_perms_cads_admin(django_user_model):
    user = django_user_model.objects.create_user(username="u7", password="pw")
    user.groups.add(_create_group("cads_admin"))
    assert is_cads_admin(user) is True


@pytest.mark.django_db
def test_perms_cads_operador(django_user_model):
    user = django_user_model.objects.create_user(username="u8", password="pw")
    user.groups.add(_create_group("cads_operador"))
    assert is_cads_operador(user) is True


@pytest.mark.django_db
def test_perms_cads_contabilidad(django_user_model):
    user = django_user_model.objects.create_user(username="u9", password="pw")
    user.groups.add(_create_group("cads_contabilidad"))
    assert is_cads_contabilidad(user) is True


@pytest.mark.django_db
def test_perms_cads_deposito(django_user_model):
    user = django_user_model.objects.create_user(username="u10", password="pw")
    user.groups.add(_create_group("cads_deposito"))
    assert is_cads_deposito(user) is True


@pytest.mark.django_db
def test_perms_cads_emisor(django_user_model):
    user = django_user_model.objects.create_user(username="u11", password="pw")
    user.groups.add(_create_group("cads_emisor"))
    assert is_cads_emisor(user) is True


@pytest.mark.django_db
def test_perms_cads_emisor_mayorista(django_user_model):
    user = django_user_model.objects.create_user(username="u12", password="pw")
    user.groups.add(_create_group("cads_emisor_mayorista"))
    assert is_cads_emisor_mayorista(user) is True


@pytest.mark.django_db
def test_perms_cads_responsable_comercial(django_user_model):
    user = django_user_model.objects.create_user(username="u13", password="pw")
    user.groups.add(_create_group("cads_responsable_comercial"))
    assert is_cads_responsable_comercial(user) is True


# ---------------------------------------------------------------------------
# has_module_access
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_has_module_arreglos_true(django_user_model):
    user = django_user_model.objects.create_user(username="har1", password="pw")
    user.groups.add(_create_group("arreglos_consultor"))
    assert has_module_access(user, "arreglos") is True


@pytest.mark.django_db
def test_has_module_arreglos_false_sin_grupo(django_user_model):
    user = django_user_model.objects.create_user(username="har2", password="pw")
    assert has_module_access(user, "arreglos") is False


@pytest.mark.django_db
def test_has_module_cads_true(django_user_model):
    user = django_user_model.objects.create_user(username="hc1", password="pw")
    user.groups.add(_create_group("cads_deposito"))
    assert has_module_access(user, "cads") is True


@pytest.mark.django_db
def test_has_module_cads_false_sin_grupo(django_user_model):
    user = django_user_model.objects.create_user(username="hc2", password="pw")
    assert has_module_access(user, "cads") is False


@pytest.mark.django_db
def test_has_module_modulo_invalido(django_user_model):
    user = django_user_model.objects.create_user(username="hinv", password="pw")
    user.groups.add(_create_group("arreglos_admin"))
    assert has_module_access(user, "otro_modulo") is False


@pytest.mark.django_db
def test_has_module_usuario_inactivo(django_user_model):
    user = django_user_model.objects.create_user(username="hinact", password="pw", is_active=False)
    user.groups.add(_create_group("arreglos_admin"))
    assert has_module_access(user, "arreglos") is False


@pytest.mark.django_db
def test_has_module_none_user():
    assert has_module_access(None, "arreglos") is False


# ---------------------------------------------------------------------------
# sync_grupos (roles.py)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sync_grupos_asigna_grupo_ar(django_user_model):
    user = django_user_model.objects.create_user(username="sg1", password="pw")
    _create_group("arreglos_admin")
    sync_grupos(user, "arreglos_admin", None)
    assert user.groups.filter(name="arreglos_admin").exists()


@pytest.mark.django_db
def test_sync_grupos_asigna_grupo_cads(django_user_model):
    user = django_user_model.objects.create_user(username="sg2", password="pw")
    _create_group("cads_operador")
    sync_grupos(user, None, "cads_operador")
    assert user.groups.filter(name="cads_operador").exists()


@pytest.mark.django_db
def test_sync_grupos_reemplaza_grupo_anterior(django_user_model):
    user = django_user_model.objects.create_user(username="sg3", password="pw")
    _create_group("arreglos_admin")
    _create_group("arreglos_operador")
    user.groups.add(Group.objects.get(name="arreglos_admin"))
    sync_grupos(user, "arreglos_operador", None)
    assert not user.groups.filter(name="arreglos_admin").exists()
    assert user.groups.filter(name="arreglos_operador").exists()


@pytest.mark.django_db
def test_sync_grupos_preserva_grupos_no_gestionados(django_user_model):
    user = django_user_model.objects.create_user(username="sg4", password="pw")
    otro_grupo = _create_group("grupo_externo")
    user.groups.add(otro_grupo)
    _create_group("arreglos_admin")
    sync_grupos(user, "arreglos_admin", None)
    assert user.groups.filter(name="grupo_externo").exists()
    assert user.groups.filter(name="arreglos_admin").exists()


@pytest.mark.django_db
def test_sync_grupos_sin_grupos_queda_vacio(django_user_model):
    user = django_user_model.objects.create_user(username="sg5", password="pw")
    _create_group("arreglos_admin")
    user.groups.add(Group.objects.get(name="arreglos_admin"))
    sync_grupos(user, None, None)
    assert not user.groups.filter(name="arreglos_admin").exists()
