from django.db import migrations


def seed_configuraciones(apps, schema_editor):
    ConfiguracionSistema = apps.get_model("configuracion", "ConfiguracionSistema")
    defaults = [
        {
            "clave": "app.nombre",
            "valor": "XL Sales",
            "tipo": "string",
            "descripcion": "Nombre de la aplicación",
            "grupo": "app",
            "editable": True,
        },
        {
            "clave": "app.version",
            "valor": "1.0.0",
            "tipo": "string",
            "descripcion": "Versión actual del sistema",
            "grupo": "app",
            "editable": False,
        },
        {
            "clave": "integracion.tango.habilitado",
            "valor": "false",
            "tipo": "bool",
            "descripcion": "Habilita la sincronización con el ERP Tango",
            "grupo": "integracion.tango",
            "editable": True,
        },
    ]
    for data in defaults:
        ConfiguracionSistema.objects.get_or_create(
            clave=data["clave"],
            defaults={k: v for k, v in data.items() if k != "clave"},
        )


def reverse_seed(apps, schema_editor):
    pass  # no revertir seed en rollback


class Migration(migrations.Migration):

    dependencies = [
        ("configuracion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_configuraciones, reverse_seed),
    ]
