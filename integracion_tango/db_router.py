"""
Router de solo lectura para el ERP Tango (alias 'tango').

Todas las consultas de integracion_tango van a 'tango'.
Nunca se escribe en Tango ni se crean migraciones.
"""


class TangoRouter:
    route_app_labels = {"integracion_tango"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "tango"
        return None

    def db_for_write(self, model, **hints):
        # Tango es readonly — bloquear escrituras a nivel router
        if model._meta.app_label in self.route_app_labels:
            return None
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Nunca migrar en Tango
        if app_label in self.route_app_labels:
            return False
        return None
