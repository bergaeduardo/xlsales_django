import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfiguracionSistema",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")),
                ("clave", models.CharField(db_index=True, max_length=100, unique=True, verbose_name="clave")),
                ("valor", models.TextField(verbose_name="valor")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("string", "Texto"),
                            ("int", "Entero"),
                            ("bool", "Booleano"),
                            ("json", "JSON"),
                            ("decimal", "Decimal"),
                        ],
                        default="string",
                        max_length=20,
                        verbose_name="tipo de dato",
                    ),
                ),
                ("descripcion", models.CharField(blank=True, max_length=255, verbose_name="descripción")),
                ("grupo", models.CharField(blank=True, db_index=True, max_length=50, verbose_name="grupo")),
                ("editable", models.BooleanField(default=True, verbose_name="editable")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="creado por",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="modificado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "configuración del sistema",
                "verbose_name_plural": "configuraciones del sistema",
                "ordering": ["grupo", "clave"],
                "abstract": False,
            },
        ),
    ]
