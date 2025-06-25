from django.urls import path

from . import views

app_name = "saas"

urlpatterns = [
    # Subscription Management
    path(
        "subscription/",
        views.SubscriptionDashboardView.as_view(),
        name="subscription_dashboard",
    ),
    path(
        "subscription/upgrade/<int:plan_id>/", views.upgrade_plan, name="upgrade_plan"
    ),
    path(
        "subscription/downgrade/<int:plan_id>/",
        views.downgrade_plan,
        name="downgrade_plan",
    ),
    path("subscription/cancel/", views.cancel_subscription, name="cancel_subscription"),
    # Billing & Invoices
    path("billing/", views.billing_dashboard, name="billing_dashboard"),
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:invoice_id>/", views.invoice_detail, name="invoice_detail"),
    # Usage Analytics
    path("usage/", views.usage_analytics, name="usage_analytics"),
    path("usage/api/", views.usage_data_api, name="usage_data_api"),
    # Organization Management
    path("organization/", views.organization_settings, name="organization_settings"),
    path(
        "organization/branding/",
        views.organization_branding,
        name="organization_branding",
    ),
    path("organization/users/", views.organization_users, name="organization_users"),
    # Pricing
    path("pricing/", views.PricingView.as_view(), name="pricing"),
    # API Endpoints
    path(
        "api/subscription/create/",
        views.create_subscription_api,
        name="create_subscription_api",
    ),
    path(
        "api/subscription/modify/",
        views.modify_subscription_api,
        name="modify_subscription_api",
    ),
    path("api/usage/current/", views.current_usage_api, name="current_usage_api"),
    path(
        "api/features/check/<str:feature_name>/",
        views.check_feature_api,
        name="check_feature_api",
    ),
    # Webhooks
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
    # Onboarding
    path("onboarding/", views.saas_onboarding, name="onboarding"),
    path("onboarding/complete/", views.complete_onboarding, name="complete_onboarding"),
]
