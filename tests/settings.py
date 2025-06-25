# -*- coding: utf-8 -*-
"""
Test Settings for Solutio 360 PWA Project
=========================================

Optimized test settings for maximum performance and reliability.
Based on best practices from Django, pytest-django, and enterprise projects.
"""

import tempfile

from solutio_360.settings.base import *

# ==========================================
# TESTING CONFIGURATION
# ==========================================

# Debug should be False in tests for performance
DEBUG = False
TEMPLATE_DEBUG = False

# Test Database - In-memory SQLite for speed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}


# Disable migrations for tests (much faster)
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# ==========================================
# CACHE CONFIGURATION
# ==========================================

# Use local memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
}

# ==========================================
# MEDIA AND STATIC FILES
# ==========================================

# Use temporary directories for test media
MEDIA_ROOT = tempfile.mkdtemp()
STATIC_ROOT = tempfile.mkdtemp()

# Disable static file collection during tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# ==========================================
# EMAIL CONFIGURATION
# ==========================================

# Use locmem backend for email testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ==========================================
# CELERY CONFIGURATION
# ==========================================

# Execute tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# ==========================================
# SECURITY SETTINGS (Relaxed for Testing)
# ==========================================

# Password hashing - use fastest hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# CSRF and session settings
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "ERROR",  # Only show errors in tests
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# ==========================================
# TEST-SPECIFIC SETTINGS
# ==========================================

# Disable unnecessary middleware for tests
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Reduce template context processors for speed
TEMPLATES[0]["OPTIONS"]["context_processors"] = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
]

# ==========================================
# PWA TEST SETTINGS
# ==========================================

# PWA settings for testing
PWA_APP_NAME = "Solutio 360 Test"
PWA_APP_DESCRIPTION = "Test version of Solutio 360 PWA"
PWA_APP_THEME_COLOR = "#000000"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_START_URL = "/"
PWA_APP_DISPLAY = "standalone"

# ==========================================
# API TEST SETTINGS
# ==========================================

# REST framework settings for testing
REST_FRAMEWORK["TEST_REQUEST_DEFAULT_FORMAT"] = "json"
REST_FRAMEWORK["TEST_REQUEST_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

# Rate limiting disabled for tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# ==========================================
# PERFORMANCE TEST SETTINGS
# ==========================================

# Database query optimization for tests
DATABASES["default"]["OPTIONS"].update(
    {
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "charset": "utf8mb4",
    }
)

# Optimize for test performance
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB

# ==========================================
# EXTERNAL SERVICES (Mocked in Tests)
# ==========================================

# Mock external services
GOOGLE_ANALYTICS_ID = "TEST-GA-ID"
SENTRY_DSN = None  # Disable Sentry in tests

# Mock payment gateway
PAYMENT_GATEWAY_URL = "http://mock-payment-gateway.test"

# Mock email service
EMAIL_SERVICE_API_KEY = "test-api-key"

# ==========================================
# TEST DATA CONFIGURATION
# ==========================================

# Test-specific constants
TEST_DATA_DIR = BASE_DIR / "tests" / "data"
TEST_FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

# File upload settings for tests
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# ==========================================
# PERFORMANCE MONITORING
# ==========================================

# Django Silk for performance profiling (only in test mode)
if "test" in sys.argv:
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")

# ==========================================
# INTERNATIONALIZATION (Simplified)
# ==========================================

# Use English only for tests
LANGUAGE_CODE = "en-us"
USE_I18N = False
USE_TZ = True
TIME_ZONE = "UTC"

# ==========================================
# CUSTOM TEST SETTINGS
# ==========================================

# Test environment flag
TESTING = True

# Mock settings for external integrations
MOCK_EXTERNAL_APIS = True
SKIP_MIGRATIONS = True

# Test database creation optimizations
DATABASES["default"]["TEST"] = {
    "NAME": None,  # Use in-memory database
    "CHARSET": None,
    "COLLATION": None,
    "CREATE_DB": False,
    "USER": None,
    "PASSWORD": None,
    "TBLSPACE": None,
    "TBLSPACE_TMP": None,
}

# Test runner configuration
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Coverage exclusions
COVERAGE_MODULE_EXCLUDES = [
    "tests$",
    "settings$",
    "urls$",
    "locale$",
    "migrations",
    "fixtures",
    "admin$",
    "management",
    "vendors",
    "venv",
    "env",
]
