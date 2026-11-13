"""Serializers para el módulo de Pedidos de Reparación (US #975)."""
import logging

from rest_framework import serializers

from .models import DetalleArticuloArreglo, EstadoArreglo, PedidoArreglo

logger = logging.getLogger(__name__)


class DetalleArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleArticuloArreglo
        fields = ["id_detalle_articulo", "codigo_articulo", "cantidad", "observacion"]


class PedidoArregloListSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = PedidoArreglo
        fields = [
            "id", "estado", "estado_display",
            "cliente", "email", "telefono",
            "fecha_solicitud", "fecha_de_compra",
            "articulo", "descripcion",
        ]


class PedidoArregloDetailSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    detalles_articulo = DetalleArticuloSerializer(many=True, read_only=True)

    class Meta:
        model = PedidoArreglo
        fields = "__all__"
        extra_fields = ["estado_display", "detalles_articulo"]

    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)
        return fields + ["estado_display", "detalles_articulo"]


class PedidoArregloCreateSerializer(serializers.ModelSerializer):
    estado = serializers.IntegerField(
        required=False,
        default=EstadoArreglo.BORRADOR,
    )

    class Meta:
        model = PedidoArreglo
        fields = [
            "estado", "cliente", "email", "telefono",
            "fecha_solicitud", "fecha_de_compra",
            "articulo", "descripcion", "observaciones", "recibido",
            "bolsin", "bolsin_egreso",
            "forro", "cierre", "costura", "correa", "herraje", "otro",
            "txt_forro", "txt_cierre", "txt_costura", "txt_correa", "txt_herraje", "txt_otro",
            "id_comprobante",
        ]

    def validate_estado(self, value):
        valid_values = [c[0] for c in EstadoArreglo.choices]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Estado inválido: {value}. Opciones: {valid_values}"
            )
        return value

    def validate_id_comprobante(self, value):
        if value is not None and not isinstance(value, int):
            raise serializers.ValidationError("id_comprobante debe ser un entero.")
        return value


class PedidoArregloUpdateSerializer(PedidoArregloCreateSerializer):
    estado = serializers.IntegerField(required=False)


class CambiarEstadoSerializer(serializers.Serializer):
    estado = serializers.IntegerField()

    def validate_estado(self, value):
        valid_values = [c[0] for c in EstadoArreglo.choices]
        if value not in valid_values:
            raise serializers.ValidationError(
                f"Estado inválido: {value}. Opciones: {valid_values}"
            )
        return value
