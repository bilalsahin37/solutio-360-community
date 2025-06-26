# -*- coding: utf-8 -*-
"""
Test Configuration for Solutio 360 PWA Project
===============================================

World-class testing configuration inspired by:
- Django testing best practices
- Google's Test Engineering team guidelines
- Microsoft Azure testing standards
- Netflix's reliability engineering practices
"""

import os
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings

# Test Database Configuration
TEST_DATABASE_CONFIG = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

# Test Cache Configuration
TEST_CACHE_CONFIG = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Test Media and Static Files
TEST_MEDIA_ROOT = tempfile.mkdtemp()
TEST_STATIC_ROOT = tempfile.mkdtemp()

# Test Email Backend
TEST_EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Performance Test Settings
PERFORMANCE_TEST_CONFIG = {
    "MAX_RESPONSE_TIME_MS": 500,
    "MAX_DATABASE_QUERIES": 10,
    "MAX_MEMORY_USAGE_MB": 100,
    "MIN_CACHE_HIT_RATIO": 0.8,
}

# PWA Test Configuration
PWA_TEST_CONFIG = {
    "SERVICE_WORKER_PATH": "/static/js/sw.js",
    "MANIFEST_PATH": "/manifest.json",
    "OFFLINE_FALLBACK_PATH": "/offline/",
    "CACHE_NAMES": ["static-cache-v1", "dynamic-cache-v1"],
}

# API Test Configuration
API_TEST_CONFIG = {
    "BASE_URL": "/api/v1/",
    "AUTH_HEADER_PREFIX": "Bearer",
    "RATE_LIMIT_REQUESTS": 1000,
    "RATE_LIMIT_WINDOW": 3600,
}

# Security Test Configuration
SECURITY_TEST_CONFIG = {
    "ALLOWED_HOSTS": ["testserver", "localhost", "127.0.0.1"],
    "CSRF_COOKIE_SECURE": False,  # For testing
    "SESSION_COOKIE_SECURE": False,  # For testing
    "SECURE_SSL_REDIRECT": False,  # For testing
}


# Test Settings Override
@override_settings(
    DATABASES=TEST_DATABASE_CONFIG,
    CACHES=TEST_CACHE_CONFIG,
    MEDIA_ROOT=TEST_MEDIA_ROOT,
    STATIC_ROOT=TEST_STATIC_ROOT,
    EMAIL_BACKEND=TEST_EMAIL_BACKEND,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    **SECURITY_TEST_CONFIG,
)
class TestConfigMixin:
    """
    Mixin class for test configuration
    """

    pass


# Test Data Factory Configuration
TEST_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
}

TEST_COMPLAINT_DATA = {
    "title": "Test Complaint",
    "description": "This is a test complaint description",
    "priority": "MEDIUM",
    "status": "SUBMITTED",
}

# Mock Services Configuration
MOCK_SERVICES = {
    "email_service": "tests.mocks.email_service.MockEmailService",
    "cache_service": "tests.mocks.cache_service.MockCacheService",
    "notification_service": "tests.mocks.notification_service.MockNotificationService",
}

# Test Coverage Configuration
COVERAGE_CONFIG = {
    "source": ["core", "complaints", "reports", "users"],
    "omit": [
        "*/migrations/*",
        "*/tests/*",
        "*/venv/*",
        "manage.py",
        "settings/*",
    ],
    "minimum_coverage": 80,
}

# Load Testing Configuration
LOAD_TEST_CONFIG = {
    "concurrent_users": 10,
    "test_duration_seconds": 60,
    "ramp_up_time_seconds": 10,
    "endpoints": [
        "/api/v1/complaints/",
        "/dashboard/",
        "/reports/",
    ],
}
