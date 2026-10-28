from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third party
    "axes",
    "simple_history",
    "rest_framework",
    # Local
    "core.apps.CoreConfig",
    "compartidos.apps.CompartidosConfig",
    "arreglos.apps.ArreglosConfig",
    "cads.apps.CadsConfig",
    "integracion_tango.apps.IntegracionTangoConfig",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# =============================================================================
# Bases de datos
# =============================================================================
DATABASES = {
    # default (PostgreSQL) — User/grupos/permisos/sesiones + PerfilUsuario (nuevo)
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql_psycopg2"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", default="5432"),
    },
    # xlsales (SQL Server) — datos existentes de XLSales (managed=False)
    "xlsales": {
        "ENGINE": "mssql",
        "NAME": env("XLSALES_DB_NAME"),
        "USER": env("XLSALES_DB_USER"),
        "PASSWORD": env("XLSALES_DB_PASSWORD"),
        "HOST": env("XLSALES_DB_HOST"),
        "PORT": env("XLSALES_DB_PORT", default="1433"),
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
        },
    },
    # tango (SQL Server readonly) — ERP externo, validación NC
    "tango": {
        "ENGINE": "mssql",
        "NAME": env("TANGO_DB_NAME"),
        "USER": env("TANGO_DB_USER"),
        "PASSWORD": env("TANGO_DB_PASSWORD"),
        "HOST": env("TANGO_DB_HOST"),
        "PORT": env("TANGO_DB_PORT", default="1433"),
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
        },
    },
}

DATABASE_ROUTERS = [
    "core.db_router.XlsalesRouter",
    "integracion_tango.db_router.TangoRouter",
]

# =============================================================================
# Internacionalización
# =============================================================================
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# =============================================================================
# Archivos estáticos y media
# =============================================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Email
# =============================================================================
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="XLSales <noreply@xl.com.ar>")

# =============================================================================
# Seguridad (defaults dev-safe; production.py los sobreescribe)
# =============================================================================
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)

# =============================================================================
# django-axes (protección brute-force)
# =============================================================================
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hora
AXES_LOCKOUT_CALLABLE = None

# =============================================================================
# DRF
# =============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
}

# =============================================================================
# Login / Logout
# =============================================================================
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"

# =============================================================================
# Logging
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "xlsales.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "arreglos": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "cads": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "core": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
    },
}
