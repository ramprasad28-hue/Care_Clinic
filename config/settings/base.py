"""
Base settings shared by all environments.

Secrets and host configuration are read from environment variables via
python-dotenv (see .env.example for the documented names/placeholders).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from the project root if present (never committed).
load_dotenv(BASE_DIR / ".env")

# --- Core security / host configuration (from environment) ---
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()
]

# --- Application definition ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "accounts.apps.AccountsConfig",
    "clinic.apps.ClinicConfig",
    "appointments.apps.AppointmentsConfig",
    "dashboards.apps.DashboardsConfig",
    "website.apps.WebsiteConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Custom user model (must be set before the first migration) ---
AUTH_USER_MODEL = "accounts.User"

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization / timezone ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --- Static & media files ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Authentication redirects ---
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# --- Authentication backends (email is USERNAME_FIELD on accounts.User) ---
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# --- Email (used by password reset). Overridden to the console backend in
# development; production must supply a real backend/credentials via env. ---
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Care_Clinic <no-reply@careclinic.local>")

# --- Database ---
# DB_ENGINE selects the backend. Default is mysql (the intended primary
# database, ADR-003). Set DB_ENGINE=sqlite ONLY as a documented local
# fallback while MySQL credentials are unavailable (see docs/decisions.md).
DB_ENGINE = os.environ.get("DB_ENGINE", "mysql").strip().lower()

if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DATABASE_NAME", ""),
            "USER": os.environ.get("DATABASE_USER", ""),
            "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
            "HOST": os.environ.get("DATABASE_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DATABASE_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            "TEST": {
                "CHARSET": "utf8mb4",
                "COLLATION": "utf8mb4_unicode_ci",
            },
        }
    }
