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
            name="PuntoVenta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Fecha de modificación"
                    ),
                ),
                (
                    "codigo",
                    models.CharField(
                        max_length=10, unique=True, verbose_name="código"
                    ),
                ),
                (
                    "nombre",
                    models.CharField(max_length=100, verbose_name="nombre"),
                ),
                (
                    "direccion",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="dirección"
                    ),
                ),
                (
                    "telefono",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="teléfono"
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(default=True, verbose_name="activo"),
                ),
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
                "verbose_name": "punto de venta",
                "verbose_name_plural": "puntos de venta",
                "ordering": ["codigo"],
            },
        ),
        migrations.AddConstraint(
            model_name="puntoventa",
            constraint=models.UniqueConstraint(
                fields=["codigo"], name="uq_puntoventa_codigo"
            ),
        ),
    ]
