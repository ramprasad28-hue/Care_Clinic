"""Regression tests for ``config.settings.production`` and entry points.

These tests verify the documented behaviour from Phase 2 (README §3) and the
Phase 8 audit:

* production refuses to start without ``DJANGO_SECRET_KEY`` /
  ``DJANGO_ALLOWED_HOSTS`` (startup failure, not a runtime crash);
* the documented transport/cookie/misc hardening flags have exactly the
  values in ``config/settings/production.py``;
* production does not inherit the development fallbacks and ``config.wsgi``
  defaults to production.

Isolation strategy
------------------
Production settings validate configuration **during module import**, so the
tests import the settings module inside a throwaway interpreter
(``subprocess``) whose environment contains only dummy test values.

python-dotenv-aware isolation: ``config.settings.base`` calls
``load_dotenv(BASE_DIR / ".env")``. ``load_dotenv`` never overrides variables
already present in the environment, so for "missing configuration" tests the
child is given an **explicit empty value** (``DJANGO_SECRET_KEY=""`` /
``DJANGO_ALLOWED_HOSTS=""``) — a value which a local ``.env`` therefore
cannot silently satisfy. The parent's own environment (which the test
runner has already populated from a local ``.env``) is stripped of all
``DJANGO_*``/``DATABASE_*`` variables before being handed to the child.

Secrecy: no child ever echoes the secret value itself — only a SHA-256
digest, comparable with the digest of the dummy value known to the parent —
and only explicit dummy credentials reach the child.
"""
import hashlib
import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from django.test import SimpleTestCase

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCTION_MODULE = "config.settings.production"
DEVELOPMENT_MODULE = "config.settings.development"
WSGI_MODULE = "config.wsgi"

# Documented production hardening (config/settings/production.py, §7 of
# docs/architecture.md). These are the *implementation* values; the tests
# below pin them so accidental regressions are caught.
HSTS_SECONDS = 31536000  # 1 year
REVERSE_PROXY_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DEVELOPMENT_FALLBACK_SECRET = "django-insecure-dev-only-key-not-for-production"
DEVELOPMENT_FALLBACK_HOSTS = ["127.0.0.1", "localhost"]

# Dummy values used exclusively inside the child environments. Never a real
# credential, and never passed on a command line (env vars only).
DUMMY_SECRET = "dummy-production-secret-key-for-regression-tests"
DUMMY_HOST = "dummy-host-for-regression-tests.example.internal"
DUMMY_SMTP_PASSWORD = "dummy-smtp-password-for-regression-tests"
DUMMY_CA_PATH = "dummy-ca-bundle.pem"
DUMMY_SMTP_HOST = "smtp.dummy.invalid"

SECURITY_ENV_NAMES = (
    "DJANGO_SETTINGS_MODULE",
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DB_ENGINE",
    "DATABASE_SSL_CA",
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "EMAIL_USE_TLS",
    "EMAIL_USE_SSL",
    "EMAIL_TIMEOUT",
    "DEFAULT_FROM_EMAIL",
)

# Runs inside the child interpreter.
#   argv[1] = module to import (settings module or entrypoint)
#   argv[2] = mode: "flags" (dump hardening values) or "wsgi-default"
# Protocol: prints exactly one meaningful first line and exits 0.
#   FAIL:<ExceptionType>:<variable marker>  -> refused startup
#   OK:<json of selected settings>          -> started cleanly
#   WSGI:<resolved DJANGO_SETTINGS_MODULE>  -> entrypoint default
# The child prints digests, never secret values (SMTP password included).
_CHILD_CODE = textwrap.dedent(
    """
    import hashlib, json, os, sys

    module, mode = sys.argv[1], sys.argv[2]
    markers = (
        "SECRET_KEY", "ALLOWED_HOSTS", "EMAIL_USE_TLS", "EMAIL_PORT",
        "EMAIL_TIMEOUT",
    )

    try:
        __import__(module)
    except Exception as exc:
        text = str(exc)
        print(
            "FAIL:%s:%s"
            % (
                type(exc).__name__,
                next((m for m in markers if m in text), "OTHER"),
            )
        )
        sys.exit(0)

    if mode == "wsgi-default":
        print("WSGI:" + os.environ.get("DJANGO_SETTINGS_MODULE", "<unset>"))
        sys.exit(0)

    from django.conf import settings

    # development.py does not define every hardening flag (e.g.
    # SECURE_PROXY_SSL_HEADER); read optional attrs defensively.
    def flag(name, default=None):
        try:
            return getattr(settings, name)
        except AttributeError:
            return default

    # mysqlclient accepts the TLS client configuration as an `ssl` dict plus
    # a top-level ssl_mode; get_connection_params() composes these without
    # opening any connection.
    db = settings.DATABASES["default"]
    db_kwargs_tls = None
    db_kwargs_ssl_mode = None
    if db["ENGINE"].endswith("mysql"):
        from django.db.backends.mysql.base import DatabaseWrapper as MySQLWrapper

        params = MySQLWrapper(dict(db)).get_connection_params()
        db_kwargs_tls = params.get("ssl")
        db_kwargs_ssl_mode = params.get("ssl_mode")

    payload = {
        "DEBUG": settings.DEBUG,
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "SECRET_KEY_DIGEST": hashlib.sha256(
            settings.SECRET_KEY.encode("utf-8")
        ).hexdigest(),
        "SECURE_SSL_REDIRECT": flag("SECURE_SSL_REDIRECT"),
        "SESSION_COOKIE_SECURE": flag("SESSION_COOKIE_SECURE"),
        "CSRF_COOKIE_SECURE": flag("CSRF_COOKIE_SECURE"),
        "SECURE_HSTS_SECONDS": flag("SECURE_HSTS_SECONDS"),
        "SECURE_HSTS_INCLUDE_SUBDOMAINS": flag("SECURE_HSTS_INCLUDE_SUBDOMAINS"),
        "SECURE_HSTS_PRELOAD": flag("SECURE_HSTS_PRELOAD"),
        "SECURE_PROXY_SSL_HEADER": list(settings.SECURE_PROXY_SSL_HEADER) if flag("SECURE_PROXY_SSL_HEADER") is not None else None,
        "SESSION_COOKIE_HTTPONLY": settings.SESSION_COOKIE_HTTPONLY,
        "SESSION_COOKIE_SAMESITE": settings.SESSION_COOKIE_SAMESITE,
        "CSRF_COOKIE_HTTPONLY": settings.CSRF_COOKIE_HTTPONLY,
        "CSRF_COOKIE_SAMESITE": settings.CSRF_COOKIE_SAMESITE,
        "X_FRAME_OPTIONS": flag("X_FRAME_OPTIONS"),
        "SECURE_CONTENT_TYPE_NOSNIFF": flag("SECURE_CONTENT_TYPE_NOSNIFF"),
        "SECURE_REFERRER_POLICY": flag("SECURE_REFERRER_POLICY"),
        "SETTINGS_MODULE": settings.SETTINGS_MODULE,
        "EMAIL_BACKEND": flag("EMAIL_BACKEND"),
        "EMAIL_HOST": flag("EMAIL_HOST"),
        "EMAIL_PORT": flag("EMAIL_PORT"),
        "EMAIL_HOST_USER": flag("EMAIL_HOST_USER"),
        "EMAIL_HOST_PASSWORD_DIGEST": hashlib.sha256(
            (flag("EMAIL_HOST_PASSWORD") or "").encode("utf-8")
        ).hexdigest(),
        "EMAIL_USE_TLS": flag("EMAIL_USE_TLS"),
        "EMAIL_USE_SSL": flag("EMAIL_USE_SSL"),
        "EMAIL_TIMEOUT": flag("EMAIL_TIMEOUT"),
        "DEFAULT_FROM_EMAIL": flag("DEFAULT_FROM_EMAIL"),
        "DATABASE_OPTIONS": db.get("OPTIONS"),
        "DB_SSL_KWARGS": db_kwargs_tls,
        "DB_SSL_MODE_KWARGS": db_kwargs_ssl_mode,
    }
    print("OK:" + json.dumps(payload))
    """
)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ProductionSettingsTests(SimpleTestCase):
    """Startup-failure, hardening-flag and separation guarantees of the
    production configuration, exercised in isolated child processes.
    """

    @classmethod
    def _child_env(cls):
        # Strip everything the test-runner process loaded from the real
        # .env, then hand the child a minimal, explicit environment.
        env = os.environ.copy()
        for name in SECURITY_ENV_NAMES:
            env.pop(name, None)
        # Explicit empties: python-dotenv (called inside config.settings.base)
        # never overrides pre-existing values, so a local .env cannot
        # secretly satisfy a "missing configuration" test.
        env["DJANGO_SECRET_KEY"] = ""
        env["DJANGO_ALLOWED_HOSTS"] = ""
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env

    @classmethod
    def _run_child(cls, module, mode, **overrides):
        """Import *module* in a child interpreter.

        ``mode='flags'`` imports a settings module (it is also preseeded as
        ``DJANGO_SETTINGS_MODULE``); ``mode='wsgi-default'`` imports an
        entrypoint with **no** ``DJANGO_SETTINGS_MODULE`` set so the
        entrypoint's ``os.environ.setdefault`` default is what engages.
        """
        env = cls._child_env()
        if mode == "flags":
            env[env_name := "DJANGO_SETTINGS_MODULE"] = module
        for key, value in overrides.items():
            env[key] = value
        return subprocess.run(
            [sys.executable, "-c", _CHILD_CODE, module, mode],
            env=env,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=90,
        )

    @classmethod
    def _first_line(cls, proc):
        output = proc.stdout.strip()
        return output.splitlines()[0] if output else "<child produced no output>"

    # -- shared successful production import (dummy credentials) ----------
    @classmethod
    def _production_flags(cls):
        """One child import of production.py with dummy credentials, reused
        by all hardening-flag assertions.
        """
        if not hasattr(cls, "_flags_cache"):
            proc = cls._run_child(
                PRODUCTION_MODULE,
                "flags",
                DJANGO_SECRET_KEY=DUMMY_SECRET,
                DJANGO_ALLOWED_HOSTS=DUMMY_HOST,
            )
            line = cls._first_line(proc)
            if not line.startswith("OK:"):
                cls._flags_cache = None
            else:
                cls._flags_cache = json.loads(line.split(":", 1)[1])
        return cls._flags_cache

    @classmethod
    def _development_flags(cls):
        """Child import of development.py with no credentials provided
        (explicit empties), showing the documented dev-only fallbacks.
        """
        if not hasattr(cls, "_dev_cache"):
            proc = cls._run_child(DEVELOPMENT_MODULE, "flags")
            line = cls._first_line(proc)
            cls._dev_cache = (
                json.loads(line.split(":", 1)[1]) if line.startswith("OK:") else None
            )
        return cls._dev_cache

    @classmethod
    def _ok_flags(cls, **env_extra):
        """Child import of production.py with per-test dummy overrides;
        asserts the clean-start protocol and returns the parsed flags.
        """
        proc = cls._run_child(
            PRODUCTION_MODULE,
            "flags",
            DJANGO_SECRET_KEY=DUMMY_SECRET,
            DJANGO_ALLOWED_HOSTS=DUMMY_HOST,
            **env_extra,
        )
        line = cls._first_line(proc)
        if not line.startswith("OK:"):
            raise AssertionError(
                "production import failed in child: %s\nstderr: %s"
                % (line, (proc.stderr or "")[-1200:])
            )
        return json.loads(line.split(':', 1)[1])

    @classmethod
    def _failure_line(cls, **env_extra):
        """Child import of production.py expected to refuse startup."""
        proc = cls._run_child(
            PRODUCTION_MODULE,
            "flags",
            DJANGO_SECRET_KEY=DUMMY_SECRET,
            DJANGO_ALLOWED_HOSTS=DUMMY_HOST,
            **env_extra,
        )
        return cls._first_line(proc)

    # ------------------------------------------------------------------
    # A. Required configuration
    # ------------------------------------------------------------------
    def test_startup_fails_without_secret_key(self):
        """DJANGO_SECRET_KEY missing (explicitly empty; .env cannot fill it)
        -> ImproperlyConfigured at import, naming the missing variable.
        """
        proc = self._run_child(
            PRODUCTION_MODULE,
            "flags",
            DJANGO_SECRET_KEY="",
            DJANGO_ALLOWED_HOSTS=DUMMY_HOST,
        )
        line = self._first_line(proc)
        self.assertTrue(
            line == "FAIL:ImproperlyConfigured:SECRET_KEY",
            f"unexpected child outcome: {line}",
        )

    def test_startup_fails_without_allowed_hosts(self):
        proc = self._run_child(
            PRODUCTION_MODULE,
            "flags",
            DJANGO_SECRET_KEY=DUMMY_SECRET,
            DJANGO_ALLOWED_HOSTS="",
        )
        line = self._first_line(proc)
        self.assertTrue(
            line == "FAIL:ImproperlyConfigured:ALLOWED_HOSTS",
            f"unexpected child outcome: {line}",
        )

    def test_startup_fails_fast_on_secret_key_even_if_hosts_also_missing(self):
        """Both missing: config fails on the first documented requirement."""
        proc = self._run_child(PRODUCTION_MODULE, "flags")
        line = self._first_line(proc)
        self.assertTrue(
            line == "FAIL:ImproperlyConfigured:SECRET_KEY",
            f"unexpected child outcome: {line}",
        )

    def test_production_loads_with_dummy_values(self):
        """With both required values supplied, production imports cleanly,
        keeps DEBUG off, parses the host list and uses the provided key.
        """
        flags = self._production_flags()
        from django.core.exceptions import ImproperlyConfigured

        self.assertIsNotNone(flags, "production import failed in child process")
        self.assertIs(flags["DEBUG"], False)
        self.assertEqual(flags["ALLOWED_HOSTS"], [DUMMY_HOST])
        self.assertEqual(flags["SECRET_KEY_DIGEST"], digest(DUMMY_SECRET))
        self.assertNotEqual(
            flags["SECRET_KEY_DIGEST"],
            digest(DEVELOPMENT_FALLBACK_SECRET),
            "production must never fall back to the development secret key",
        )

    # ------------------------------------------------------------------
    # B. Production security flags
    # ------------------------------------------------------------------
    def test_transport_security_flags(self):
        flags = self._production_flags()
        self.assertIsNotNone(flags)
        self.assertIs(flags["SECURE_SSL_REDIRECT"], True)
        self.assertIs(flags["SESSION_COOKIE_SECURE"], True)
        self.assertIs(flags["CSRF_COOKIE_SECURE"], True)
        self.assertEqual(flags["SECURE_HSTS_SECONDS"], HSTS_SECONDS)
        self.assertIs(flags["SECURE_HSTS_INCLUDE_SUBDOMAINS"], True)
        self.assertIs(flags["SECURE_HSTS_PRELOAD"], True)
        self.assertEqual(list(flags["SECURE_PROXY_SSL_HEADER"]), list(REVERSE_PROXY_HEADER))

    def test_cookie_policy_flags(self):
        flags = self._production_flags()
        self.assertIsNotNone(flags)
        self.assertIs(flags["SESSION_COOKIE_HTTPONLY"], True)
        self.assertEqual(flags["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertEqual(flags["CSRF_COOKIE_SAMESITE"], "Lax")
        # CSRF_COOKIE_HTTPONLY is not overridden in production.py: the
        # Django default (False) is retained — rendering the CSRF cookie
        # HttpOnly would break the non-JS CSRF token flow. Pinned as-is.
        self.assertIs(flags["CSRF_COOKIE_HTTPONLY"], False)

    def test_misc_hardening_flags(self):
        flags = self._production_flags()
        self.assertIsNotNone(flags)
        self.assertEqual(flags["X_FRAME_OPTIONS"], "DENY")
        self.assertIs(flags["SECURE_CONTENT_TYPE_NOSNIFF"], True)
        self.assertEqual(flags["SECURE_REFERRER_POLICY"], "same-origin")

    # ------------------------------------------------------------------
    # C. Development-versus-production separation
    # ------------------------------------------------------------------
    def test_production_does_not_use_development_fallbacks(self):
        """Both fallbacks of development.py (secret key, hosts) are absent
        from a production start, and DEBUG stays hard-False there.
        """
        flags = self._production_flags()
        dev = self._development_flags()  # for reference/contrast
        self.assertIsNotNone(flags)
        self.assertNotEqual(flags["SECRET_KEY_DIGEST"], digest(DEVELOPMENT_FALLBACK_SECRET))
        self.assertNotEqual(flags["ALLOWED_HOSTS"], DEVELOPMENT_FALLBACK_HOSTS)
        self.assertNotEqual(flags["DEBUG"], dev["DEBUG"] if dev else True)

    def test_development_still_provides_documented_fallbacks(self):
        """The contrast case: with no configuration at all, development
        starts (that is its documented purpose) using the dev-only fallback
        key/hosts and DEBUG=True.
        """
        dev = self._development_flags()
        self.assertIsNotNone(dev)
        self.assertIs(dev["DEBUG"], True)
        self.assertEqual(dev["SECRET_KEY_DIGEST"], digest(DEVELOPMENT_FALLBACK_SECRET))
        self.assertEqual(dev["ALLOWED_HOSTS"], DEVELOPMENT_FALLBACK_HOSTS)

    def test_wsgi_defaults_to_production(self):
        """config.wsgi resolves DJANGO_SETTINGS_MODULE to production when
        the environment does not supply one (README §3).
        """
        proc = self._run_child(
            WSGI_MODULE,
            "wsgi-default",
            DJANGO_SECRET_KEY=DUMMY_SECRET,
            DJANGO_ALLOWED_HOSTS=DUMMY_HOST,
        )
        line = self._first_line(proc)
        self.assertTrue(
            line == f"WSGI:{PRODUCTION_MODULE}",
            f"unexpected wsgi default: {line}",
        )

    # ------------------------------------------------------------------
    # A. Email configuration (environment-driven, D1)
    # ------------------------------------------------------------------
    def test_default_email_settings_are_django_smtp_defaults(self):
        """Without any EMAIL_* variable, production keeps Django's
        documented SMTP defaults — tests must not assume a provider.
        """
        flags = self._ok_flags()
        self.assertEqual(
            flags["EMAIL_BACKEND"], "django.core.mail.backends.smtp.EmailBackend"
        )
        self.assertEqual(flags["EMAIL_HOST"], "localhost")
        self.assertEqual(flags["EMAIL_PORT"], 25)
        self.assertEqual(flags["EMAIL_HOST_USER"], "")
        self.assertEqual(flags["EMAIL_HOST_PASSWORD_DIGEST"], digest(""))
        self.assertIs(flags["EMAIL_USE_TLS"], False)
        self.assertIs(flags["EMAIL_USE_SSL"], False)
        self.assertIsNone(flags["EMAIL_TIMEOUT"])
        self.assertEqual(
            flags["DEFAULT_FROM_EMAIL"], "Care_Clinic <no-reply@careclinic.local>"
        )

    def test_explicit_email_configuration_is_honored(self):
        """A fully documented (dummy) SMTP configuration flows through
        intact — a production process can therefore run against a provider
        it configures instead of falling back to localhost:25.
        """
        flags = self._ok_flags(
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            EMAIL_HOST=DUMMY_SMTP_HOST,
            EMAIL_PORT="587",
            EMAIL_HOST_USER="dummy-smtp-user",
            EMAIL_HOST_PASSWORD=DUMMY_SMTP_PASSWORD,
            EMAIL_USE_TLS="True",
            EMAIL_USE_SSL="False",
            EMAIL_TIMEOUT="30",
            DEFAULT_FROM_EMAIL="no-reply@dummy.invalid",
        )
        self.assertEqual(
            flags["EMAIL_BACKEND"], "django.core.mail.backends.smtp.EmailBackend"
        )
        self.assertEqual(flags["EMAIL_HOST"], DUMMY_SMTP_HOST)
        self.assertNotEqual(flags["EMAIL_PORT"], 25)
        self.assertEqual(flags["EMAIL_PORT"], 587)
        self.assertEqual(flags["EMAIL_HOST_USER"], "dummy-smtp-user")
        self.assertEqual(flags["EMAIL_HOST_PASSWORD_DIGEST"], digest(DUMMY_SMTP_PASSWORD))
        self.assertIs(flags["EMAIL_USE_TLS"], True)
        self.assertIs(flags["EMAIL_USE_SSL"], False)
        self.assertEqual(flags["EMAIL_TIMEOUT"], 30.0)
        self.assertEqual(flags["DEFAULT_FROM_EMAIL"], "no-reply@dummy.invalid")

    def test_email_port_must_be_a_number(self):
        line = self._failure_line(EMAIL_PORT="not-a-number")
        self.assertEqual(line, "FAIL:ImproperlyConfigured:EMAIL_PORT")

    def test_email_timeout_must_be_a_number(self):
        line = self._failure_line(EMAIL_TIMEOUT="forever")
        self.assertEqual(line, "FAIL:ImproperlyConfigured:EMAIL_TIMEOUT")

    def test_email_use_tls_and_use_ssl_are_exclusive(self):
        line = self._failure_line(EMAIL_USE_TLS="1", EMAIL_USE_SSL="1")
        self.assertEqual(line, "FAIL:ImproperlyConfigured:EMAIL_USE_TLS")

    def test_development_console_email_backend_unchanged(self):
        dev = self._development_flags()
        self.assertIsNotNone(dev)
        self.assertEqual(
            dev["EMAIL_BACKEND"], "django.core.mail.backends.console.EmailBackend"
        )

    def test_smtp_password_never_reaches_child_output(self):
        """Failure diagnostics (stdout + stderr) of a refusing child never
        contain the SMTP credential value — digests only.
        """
        proc = self._run_child(
            PRODUCTION_MODULE,
            "flags",
            DJANGO_SECRET_KEY="",  # force the documented startup refusal
            EMAIL_HOST_PASSWORD=DUMMY_SMTP_PASSWORD,
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        self.assertNotIn(DUMMY_SMTP_PASSWORD, combined)
        self.assertIn("FAIL:ImproperlyConfigured:SECRET_KEY", (proc.stdout or "").strip())

    # ------------------------------------------------------------------
    # B. Optional MySQL TLS (D2)
    # ------------------------------------------------------------------
    _MYSQL_BASE_OPTIONS = {
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }

    def test_mysql_options_unchanged_without_ssl_ca(self):
        """No DATABASE_SSL_CA: the driver options are exactly the previous
        local configuration — no `ssl` dict, and crucially no `ssl_mode`
        either, so local connections behave precisely as before.
        """
        flags = self._ok_flags()
        options = flags["DATABASE_OPTIONS"]
        self.assertNotIn("ssl", options)
        self.assertNotIn("ssl_mode", options)
        self.assertEqual(options, self._MYSQL_BASE_OPTIONS)
        self.assertIsNone(flags["DB_SSL_KWARGS"])
        self.assertIsNone(flags["DB_SSL_MODE_KWARGS"])

    def test_mysql_options_gain_ca_and_verify_identity_with_ssl_ca(self):
        """A configured CA both supplies the CA bundle and explicitly
        requires ssl_mode=VERIFY_IDENTITY: an encrypted connection whose
        server certificate is checked against the CA *and* whose hostname
        is checked against the certificate (the legacy ssl dict alone
        would only verify the chain).
        """
        flags = self._ok_flags(DATABASE_SSL_CA=DUMMY_CA_PATH)
        options = flags["DATABASE_OPTIONS"]
        self.assertEqual(options["ssl"], {"ca": DUMMY_CA_PATH})
        self.assertEqual(options["ssl_mode"], "VERIFY_IDENTITY")
        self.assertEqual(options["charset"], "utf8mb4")
        self.assertEqual(options["init_command"], "SET sql_mode='STRICT_TRANS_TABLES'")
        # The composed driver kwargs pass both through untouched
        # (get_connection_params, no connection opened).
        self.assertEqual(flags["DB_SSL_KWARGS"], {"ca": DUMMY_CA_PATH})
        self.assertEqual(flags["DB_SSL_MODE_KWARGS"], "VERIFY_IDENTITY")

    def test_empty_and_whitespace_ssl_ca_behave_as_unset(self):
        for blank in ("", "   "):
            with self.subTest(ca=repr(blank)):
                flags = self._ok_flags(DATABASE_SSL_CA=blank)
                options = flags["DATABASE_OPTIONS"]
                self.assertNotIn("ssl", options)
                self.assertNotIn("ssl_mode", options)
                self.assertIsNone(flags["DB_SSL_KWARGS"])
                self.assertIsNone(flags["DB_SSL_MODE_KWARGS"])

    def test_sqlite_never_receives_mysql_tls_options(self):
        flags = self._ok_flags(DB_ENGINE="sqlite", DATABASE_SSL_CA=DUMMY_CA_PATH)
        self.assertIsNone(flags["DATABASE_OPTIONS"])
        self.assertIsNone(flags["DB_SSL_KWARGS"])
        self.assertIsNone(flags["DB_SSL_MODE_KWARGS"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
