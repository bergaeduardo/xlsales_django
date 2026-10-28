"""
Router de base de datos principal — XLSales → Django.

Estrategia:
- Modelos con managed=False en las apps de negocio → 'xlsales' (SQL Server existente).
- Modelos con managed=True en esas apps (ej. PerfilUsuario) → 'default' (PostgreSQL).
- Django internals (auth, sessions, etc.) → 'default' (PostgreSQL).
- Tango readonly → ver integracion_tango/db_router.py.

Por qué managed=False como señal:
  Todos los modelos que mapean tablas existentes de XLSales llevan managed=False
  en su Meta. Los modelos nuevos (PerfilUsuario, configs propias) llevan managed=True
  y deben vivir en Postgres. Esto permite mezclar ambos tipos en la misma app sin
  necesitar apps separadas ni atributos custom.
"""


class XlsalesRouter:
    route_app_labels = {"compartidos", "arreglos", "cads"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels and not model._meta.managed:
            return "xlsales"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels and not model._meta.managed:
            return "xlsales"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        app1 = obj1._meta.app_label
        app2 = obj2._meta.app_label
        all_apps = self.route_app_labels | {"auth"}
        # Relaciones dentro del ecosistema xlsales ↔ auth (cross-DB con db_constraint=False)
        if app1 in all_apps and app2 in all_apps:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Las apps de negocio solo migran en 'default' (para modelos managed=True).
        # Los managed=False nunca generan migraciones de todas formas.
        if app_label in self.route_app_labels:
            return db == "default"
        return None
