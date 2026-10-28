from django.db import models


class RolArreglos(models.TextChoices):
    ADMIN = "arreglos_admin", "Administrador Arreglos"
    EMISOR = "arreglos_emisor", "Emisor"
    FABRICA = "arreglos_fabrica", "Fábrica"
    CONSULTOR = "arreglos_consultor", "Consultor"
    DEPOSITO = "arreglos_deposito", "Depósito"


class RolCads(models.TextChoices):
    EMISOR = "cads_emisor", "Emisor"
    EMISOR_MAYORISTA = "cads_emisor_mayorista", "Emisor Mayorista"
    AUTORIZADOR = "cads_autorizador", "Autorizador"
    RECEPTOR = "cads_receptor", "Receptor"
    DEPOSITO = "cads_deposito", "Depósito"


TODOS_LOS_ROLES = [r.value for r in RolArreglos] + [r.value for r in RolCads]
