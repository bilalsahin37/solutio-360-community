# -*- coding: utf-8 -*-
"""
Analytics URLs
ML Dashboard ve API endpoint'leri için URL yapılandırması
"""

from django.urls import path

from . import api, views

app_name = "analytics"

urlpatterns = [
    # ML Dashboard
    path("ml-dashboard/", views.MLDashboardView.as_view(), name="ml_dashboard"),
    # LeewayHertz-style AI Processing Dashboard
    path("ai-processing/", views.ai_processing_dashboard, name="ai_processing_dashboard"),
    # Enterprise AI API Endpoints
    path("api/dashboard-data/", views.dashboard_data_api, name="dashboard_data_api"),
    path(
        "api/process-complaint-ai/",
        views.process_complaint_with_ai,
        name="process_complaint_ai_views",
    ),
    path(
        "api/department-routing/",
        views.department_routing_api,
        name="department_routing",
    ),
    path("api/ai-insights/", views.ai_insights_api, name="ai_insights"),
    path(
        "api/sentiment-analysis/",
        views.sentiment_analysis_api,
        name="sentiment_analysis",
    ),
    path("api/predictions/", views.prediction_api, name="predictions"),
    path("api/model-performance/", views.model_performance_api, name="model_performance"),
    path("api/auto-response/", views.auto_response_api, name="auto_response"),
    # Legacy API Endpoints
    path("api/refresh-models/", views.refresh_models_api, name="refresh_models_api"),
    path("api/export-insights/", views.export_insights_api, name="export_insights_api"),
    path(
        "api/apply-insight/<int:insight_id>/",
        views.apply_insight_api,
        name="apply_insight_api",
    ),
    path(
        "api/dismiss-insight/<int:insight_id>/",
        views.dismiss_insight_api,
        name="dismiss_insight_api",
    ),
    # 🆓 FREE AI Provider Management APIs
    path("api/ai-status/", api.free_ai_status, name="free_ai_status"),
    path("api/ai-switch/", api.switch_provider, name="switch_provider"),
    path("api/ai-tips/", api.ai_optimization_tips, name="ai_optimization_tips"),
    path("api/ai-limits/", api.provider_limits_check, name="provider_limits_check"),
    path("api/ai-test/", api.test_ai_provider, name="test_ai_provider"),
    # 🤖 Real-time AI Chat API
    path("api/chat-ai/", api.process_complaint_ai, name="chat_ai"),
    # Alternative function-based view
    path("dashboard/", views.ml_dashboard, name="ml_dashboard_function"),
]
