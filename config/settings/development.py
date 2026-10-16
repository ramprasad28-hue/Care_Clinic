"""Development settings — local work only.

Provides a safe development fallback for SECRET_KEY so the project can run
and tests can execute without a .env present. NEVER use these defaults in
production (config.settings.production enforces real secrets).
"""
import sys

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS, SECRET_KEY  # noqa: F401

DEBUG = True

# Development-only fallbacks; production refuses to run without real values.
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-dev-only-key-not-for-production"

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Password-reset emails are printed to the console during development instead
# of being sent. No real mail backend/credentials are needed locally.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Quieter, more useful test output.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "stream": sys.stdout},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
