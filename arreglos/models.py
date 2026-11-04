from django.db import models
from simple_history.models import HistoricalRecords


class EstadoArreglo(models.IntegerChoices):
    """Estados del flujo de reparación (Pedidoes.Estado, legacy)."""

    BORRADOR = 0, "Borrador"
    ENVIADO = 1, "Enviado"
    FABRICA = 2, "En Fábrica"
    REPARACION = 3, "En Reparación"
    REPARADOS = 4, "Reparados"
    TERMINADO_R = 5, "Terminado (Reparación)"
    FINALIZADO = 6, "Finalizado"
    IMPORTE_A_FAVOR = 7, "Importe a Favor"
    NC_OTORGADA = 8, "NC Otorgada"
    TERMINADO_IAF = 9, "Terminado (Importe a Favor)"


class PedidoArreglo(models.Model):
    """Tabla legacy dbXLSales.Pedidoes (managed=False, solo lectura/escritura vía ORM,
    sin cambios de esquema).

    No hereda TimeStampedModel: el esquema real (verificado contra dbXLSales) no
    tiene columnas created_at/updated_at/created_by/updated_by, y agregarlas
    rompería toda consulta con "Invalid column name". Auditoría de cambios la
    cubre HistoricalRecords (tabla histórica propia en 'default', managed=True).
    """

    id = models.AutoField(primary_key=True, db_column="Id")
    estado = models.IntegerField("estado", choices=EstadoArreglo.choices, db_column="Estado")
    usuario = models.UUIDField("usuario", null=True, blank=True, db_column="Usuario")
    bolsin = models.TextField("bolsín", null=True, blank=True, db_column="Bolsin")
    bolsin_egreso = models.TextField("bolsín egreso", null=True, blank=True, db_column="BolsinEgreso")
    fecha_solicitud = models.DateTimeField("fecha de solicitud", db_column="FechaSolicitud")
    fecha_de_compra = models.DateTimeField("fecha de compra", db_column="FechaDeCompra")
    ingreso_a_fabrica = models.DateTimeField(
        "ingreso a fábrica", null=True, blank=True, db_column="IngresoAFabrica")
    fecha_egreso = models.DateTimeField("fecha de egreso", null=True, blank=True, db_column="FechaEgreso")
    box_deposito = models.DateTimeField("box depósito", null=True, blank=True, db_column="BoxDeposito")
    numero_de_orden_de_reparacion = models.TextField(
        "N° de orden de reparación", null=True, blank=True, db_column="NumeroDeOrdenDeReparacion")
    cliente = models.TextField("cliente", null=True, blank=True, db_column="Cliente")
    email = models.TextField("email", null=True, blank=True, db_column="Email")
    telefono = models.TextField("teléfono", null=True, blank=True, db_column="Telefono")
    articulo = models.TextField("artículo", null=True, blank=True, db_column="Articulo")
    descripcion = models.TextField("descripción", null=True, blank=True, db_column="Descripcion")
    observaciones = models.TextField("observaciones", null=True, blank=True, db_column="Observaciones")
    recibido = models.TextField("recibido", null=True, blank=True, db_column="Recibido")
    encargado_que_autorizo = models.TextField(
        "encargado que autorizó", null=True, blank=True, db_column="EncargadoQueAutorizo")
    entrego = models.TextField("entregó", null=True, blank=True, db_column="Entrego")
    recibio = models.TextField("recibió", null=True, blank=True, db_column="Recibio")
    diferencias_encontradas = models.TextField(
        "diferencias encontradas", null=True, blank=True, db_column="DiferenciasEncontradas")
    forro = models.BooleanField("forro", default=False, db_column="Forro")
    cierre = models.BooleanField("cierre", default=False, db_column="Cierre")
    costura = models.BooleanField("costura", default=False, db_column="Costura")
    correa = models.BooleanField("correa", default=False, db_column="Correa")
    herraje = models.BooleanField("herraje", default=False, db_column="Herraje")
    otro = models.BooleanField("otro", default=False, db_column="Otro")
    txt_forro = models.TextField("detalle forro", null=True, blank=True, db_column="txtForro")
    txt_cierre = models.TextField("detalle cierre", null=True, blank=True, db_column="txtCierre")
    txt_costura = models.TextField("detalle costura", null=True, blank=True, db_column="txtCostura")
    txt_correa = models.TextField("detalle correa", null=True, blank=True, db_column="txtCorrea")
    txt_herraje = models.TextField("detalle herraje", null=True, blank=True, db_column="txtHerraje")
    txt_otro = models.TextField("detalle otro", null=True, blank=True, db_column="txtOtro")
    decision = models.TextField("decisión", null=True, blank=True, db_column="Decision")
    # db_column preserva el typo original "Desicion" (legacy, no modificable sin DDL).
    autorizo_decision = models.TextField(
        "autorizó decisión", null=True, blank=True, db_column="AutorizoDesicion")
    nombre_de_usuario = models.TextField(
        "nombre de usuario", null=True, blank=True, db_column="NombreDeUsuario")
    ingreso_a_box = models.DateTimeField("ingreso a box", null=True, blank=True, db_column="IngresoABox")
    id_comprobante = models.BigIntegerField("ID comprobante", db_column="IdComprobante")
    ultima_modificacion = models.UUIDField(
        "última modificación", null=True, blank=True, db_column="UltimaModificacion")
    comprobante_importe_a_favor = models.CharField(
        "comprobante importe a favor",
        max_length=50,
        null=True,
        blank=True,
        db_column="ComprobanteImporteAFavor")

    # Nota: la escritura en xlsales y la escritura histórica en default
    # NO son atómicas entre DBs — fallo del historial es silencioso (signals).
    history = HistoricalRecords()

    class Meta:
        managed = False
        db_table = "Pedidoes"
        app_label = "arreglos"
        verbose_name = "pedido de arreglo"
        verbose_name_plural = "pedidos de arreglo"
        ordering = ["-id"]

    def __str__(self):
        return f"Pedido #{self.id} — {self.cliente or 's/d'}"


class DetalleArticuloArreglo(models.Model):
    """Tabla legacy dbXLSales.DetalleArticulo (managed=False)."""

    id_detalle_articulo = models.AutoField(primary_key=True, db_column="IdDetalleArticulo")
    # PROTECT evita borrado desde Django ORM; .NET-side bypasses esta protección (db_constraint=False).
    pedido = models.ForeignKey(
        PedidoArreglo,
        on_delete=models.PROTECT,
        db_column="IdPedido",
        db_constraint=False,
        related_name="detalles_articulo",
        verbose_name="pedido"
    )
    codigo_articulo = models.CharField(
        "código de artículo", max_length=100, null=True, blank=True, db_column="CodigoArticulo")
    cantidad = models.IntegerField("cantidad", default=1, db_column="Cantidad")
    observacion = models.CharField("observación", max_length=255, null=True, blank=True, db_column="Observacion")

    # Nota: la escritura en xlsales y la escritura histórica en default
    # NO son atómicas entre DBs — fallo del historial es silencioso (signals).
    history = HistoricalRecords()

    class Meta:
        managed = False
        db_table = "DetalleArticulo"
        app_label = "arreglos"
        verbose_name = "detalle de artículo"
        verbose_name_plural = "detalles de artículo"
        ordering = ["id_detalle_articulo"]

    def __str__(self):
        return f"{self.codigo_articulo} x{self.cantidad}"

    @property
    def tiene_observacion(self):
        return bool(self.observacion.strip()) if self.observacion else False

    @classmethod
    def cantidad_total_por_pedido(cls, pedido_id):
        from django.db.models import Sum

        return cls.objects.filter(pedido_id=pedido_id).aggregate(total=Sum("cantidad")).get("total", 0)


class ChatArreglo(models.Model):
    """Tabla legacy dbXLSales.Chats (managed=False)."""

    id = models.BigAutoField(primary_key=True, db_column="Id")
    fecha = models.DateTimeField("fecha", db_column="Fecha")
    usuario = models.TextField("usuario", null=True, blank=True, db_column="Usuario")
    # PROTECT evita borrado desde Django ORM; .NET-side bypasses esta protección (db_constraint=False).
    pedido = models.ForeignKey(
        PedidoArreglo,
        on_delete=models.PROTECT,
        db_column="IdPedido",
        db_constraint=False,
        related_name="chats",
        verbose_name="pedido"
    )
    descripcion = models.TextField("descripción", null=True, blank=True, db_column="Descripcion")
    id_usuario = models.UUIDField("ID de usuario", null=True, blank=True, db_column="IdUsuario")

    # Nota: la escritura en xlsales y la escritura histórica en default
    # NO son atómicas entre DBs — fallo del historial es silencioso (signals).
    history = HistoricalRecords()

    class Meta:
        managed = False
        db_table = "Chats"
        app_label = "arreglos"
        verbose_name = "chat de arreglo"
        verbose_name_plural = "chats de arreglo"
        ordering = ["fecha"]

    def __str__(self):
        return f"Chat #{self.id} (pedido #{self.pedido_id})"