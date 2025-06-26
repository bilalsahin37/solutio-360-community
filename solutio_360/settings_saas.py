"""
SaaS-specific settings for Solutio 360
Bu dosya multi-tenant, billing ve SaaS özelliklerini içerir
"""

import os

from .settings import *

# =============================================================================
# MULTI-TENANT CONFIGURATION
# =============================================================================

# Django Tenants Configuration
SHARED_APPS = [
    "django_tenants",  # mandatory
    "saas_features",  # SaaS modelleri shared olmalı
    # Django apps
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    # Third party shared apps
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]

TENANT_APPS = [
    # Django apps
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    # Local apps (her tenant için ayrı)
    "complaints",
    "users",
    "reports",
    "analytics",
    "core",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Tenant model
TENANT_MODEL = "saas_features.Organization"
TENANT_DOMAIN_MODEL = "saas_features.OrganizationDomain"

# Database routing
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# Middleware (tenant middleware must be first)
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
] + MIDDLEWARE

# =============================================================================
# PAYMENT & BILLING CONFIGURATION
# =============================================================================

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_...")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Currency
DEFAULT_CURRENCY = "TRY"
CURRENCY_SYMBOL = "₺"

# Billing
BILLING_GRACE_PERIOD_DAYS = 3
TRIAL_PERIOD_DAYS = 14

# =============================================================================
# FEATURE FLAGS & LIMITS
# =============================================================================

# Plan-based limits
PLAN_LIMITS = {
    "free": {
        "complaints": 25,
        "users": 1,
        "api_calls": 100,
        "ml_predictions": 50,
        "storage_mb": 100,
    },
    "starter": {
        "complaints": 250,
        "users": 5,
        "api_calls": 1000,
        "ml_predictions": 500,
        "storage_mb": 1000,
    },
    "professional": {
        "complaints": 1000,
        "users": 15,
        "api_calls": 10000,
        "ml_predictions": 5000,
        "storage_mb": 5000,
    },
    "enterprise": {
        "complaints": -1,  # unlimited
        "users": -1,
        "api_calls": -1,
        "ml_predictions": -1,
        "storage_mb": -1,
    },
}

# Feature matrix
PLAN_FEATURES = {
    "free": [
        "basic_dashboard",
        "email_notifications",
        "basic_reports",
    ],
    "starter": [
        "basic_dashboard",
        "email_notifications",
        "basic_reports",
        "api_access",
        "sentiment_analysis",
        "basic_ml",
    ],
    "professional": [
        "basic_dashboard",
        "advanced_dashboard",
        "email_notifications",
        "sms_notifications",
        "basic_reports",
        "advanced_reports",
        "api_access",
        "sentiment_analysis",
        "advanced_ml",
        "real_time_analytics",
        "custom_branding",
        "integrations",
    ],
    "enterprise": [
        "basic_dashboard",
        "advanced_dashboard",
        "email_notifications",
        "sms_notifications",
        "push_notifications",
        "basic_reports",
        "advanced_reports",
        "custom_reports",
        "api_access",
        "advanced_api",
        "sentiment_analysis",
        "advanced_ml",
        "ai_insights",
        "real_time_analytics",
        "custom_branding",
        "white_labeling",
        "sso",
        "custom_domain",
        "integrations",
        "priority_support",
        "dedicated_support",
    ],
}

# =============================================================================
# API & RATE LIMITING
# =============================================================================

# DRF Configuration for SaaS
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "free": "100/day",
        "starter": "1000/day",
        "professional": "10000/day",
        "enterprise": "100000/day",
    },
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# Redis Configuration (for rate limiting)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# =============================================================================
# EMAIL & NOTIFICATIONS
# =============================================================================

# Anymail Configuration
ANYMAIL = {
    "MAILGUN_API_KEY": os.getenv("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.getenv("MAILGUN_DOMAIN"),
}
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

# Twilio Configuration (SMS)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# =============================================================================
# MONITORING & ANALYTICS
# =============================================================================

# Sentry Configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )

# Mixpanel Configuration
MIXPANEL_TOKEN = os.getenv("MIXPANEL_TOKEN")

# Google Analytics
GOOGLE_ANALYTICS_PROPERTY_ID = os.getenv("GA_PROPERTY_ID")

# =============================================================================
# SECURITY
# =============================================================================

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://app.solutio360.com",
    "https://www.solutio360.com",
]

CORS_ALLOW_CREDENTIALS = True

# CSP Configuration
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "js.stripe.com")
CSP_FRAME_SRC = ("js.stripe.com",)

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# =============================================================================
# CUSTOM DOMAIN SUPPORT
# =============================================================================

# Allowed hosts for custom domains
ALLOWED_HOSTS = [
    ".solutio360.com",
    "localhost",
    "127.0.0.1",
    ".herokuapp.com",
    ".ngrok.io",
    "*",  # Production'da kaldırılmalı
]

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

# Django Q Configuration
Q_CLUSTER = {
    "name": "solutio360_saas",
    "workers": 4,
    "recycle": 500,
    "timeout": 60,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 500,
    "cpu_affinity": 1,
    "label": "Django Q",
    "redis": REDIS_URL,
}

# Cron Jobs
CRONJOBS = [
    ("0 2 * * *", "saas_features.tasks.monthly_usage_reset"),
    ("0 1 * * *", "saas_features.tasks.check_subscription_renewals"),
    ("0 3 * * *", "saas_features.tasks.cleanup_old_data"),
    ("0 */6 * * *", "saas_features.tasks.usage_analytics_aggregation"),
]

# =============================================================================
# MULTI-LANGUAGE SUPPORT
# =============================================================================

LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

USE_I18N = True
USE_L10N = True

# =============================================================================
# FILE STORAGE & CDN
# =============================================================================

# Media files for tenants
DEFAULT_FILE_STORAGE = "django_tenants.storage.TenantFileSystemStorage"

# Static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# AWS S3 Configuration (Production)
if os.getenv("USE_S3") == "true":
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "eu-west-1")

    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/saas.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.SentryHandler",
        },
    },
    "loggers": {
        "saas_features": {
            "handlers": ["file", "console", "sentry"],
            "level": "INFO",
            "propagate": True,
        },
        "billing": {
            "handlers": ["file", "sentry"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# =============================================================================
# HEALTH CHECKS
# =============================================================================

HEALTH_CHECKS = {
    "APPLICATIONS": [
        "health_check.db",
        "health_check.cache",
        "health_check.storage",
    ],
    "CUSTOM_ENDPOINTS": [
        ("stripe", "saas_features.health_checks.stripe_health"),
        ("redis", "saas_features.health_checks.redis_health"),
    ],
}

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================

if DEBUG:
    # Development-specific settings
    CORS_ALLOW_ALL_ORIGINS = True

    # Django Debug Toolbar
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]
