from .base import *  # noqa: F401, F403

DEBUG = False

# SQLite in-memory para todos los DBs — no requiere PG ni SQL Server en CI/testing.
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    # Dummy SQLite para xlsales y tango; el router dirige lecturas managed=False a
    # 'xlsales', pero ningún test de estructura hace queries reales a esa DB.
    "xlsales": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:"},
    },
    "tango": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:"},
    },
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

AXES_ENABLED = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
