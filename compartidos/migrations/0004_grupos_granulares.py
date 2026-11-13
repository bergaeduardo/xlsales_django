from django.db import migrations

_NUEVOS_GRUPOS = [
    "arreglos_consultor",
    "arreglos_deposito",
    "arreglos_emisor",
    "arreglos_fabrica",
    "cads_contabilidad",
    "cads_deposito",
    "cads_emisor",
    "cads_emisor_mayorista",
    "cads_responsable_comercial",
]


def crear_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nombre in _NUEVOS_GRUPOS:
        Group.objects.get_or_create(name=nombre)


def eliminar_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=_NUEVOS_GRUPOS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("compartidos", "0003_rolarreglos_rolcads"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
