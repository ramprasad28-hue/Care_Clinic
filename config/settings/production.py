"""Production settings — enforce secure defaults.

Refuses to start unless a real SECRET_KEY and ALLOWED_HOSTS are provided via
the environment. Applies HTTPS/security hardening (see docs/architecture.md §7).
"""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS, SECRET_KEY  # noqa: F401

DEBUG = False

# --- Production static files ---
STORAGES = {
    "default": {
        "BACKEND": "clinic.storage.CloudinaryMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set in the environment for production."
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must be set in the environment for production."
    )

# --- HTTPS / transport security ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Misc hardening ---
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# --- Production error logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
