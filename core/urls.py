# -*- coding: utf-8 -*-
"""
Core app URL konfigürasyonu
Sistem durumu, health check ve monitoring endpoint'leri
"""

from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "core"

urlpatterns = [
    # Health Check Endpoints
    path("health/", views.HealthCheckView.as_view(), name="health_check"),
    path("ping/", views.ping_view, name="ping"),
    path("status/", views.stats_view, name="status"),
    # System Information (Admin only)
    path("system-info/", views.SystemInfoView.as_view(), name="system_info"),
    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # PWA Endpoints
    path("offline/", views.offline_view, name="offline"),
    path(
        "pwa-install-stats/",
        csrf_exempt(views.pwa_install_stats),
        name="pwa_install_stats",
    ),
    # API Endpoints
    path(
        "api/",
        include(
            [
                path("health/", views.HealthCheckView.as_view(), name="api_health"),
                path("stats/", cache_page(60 * 5)(views.stats_view), name="api_stats"),
                path("ping/", views.ping_view, name="api_ping"),
            ]
        ),
    ),
]
