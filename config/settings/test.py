from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES["default"]["NAME"] = "test_usuarios_xlsales"  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

AXES_ENABLED = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
