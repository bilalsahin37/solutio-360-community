"""
SaaS Features Utilities
Utility functions for SaaS subscription management
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def calculate_usage_limits(plan_type: str) -> Dict[str, Any]:
    """
    Calculate usage limits based on subscription plan
    """
    limits = {
        "free": {
            "complaints_per_month": 25,
            "users": 1,
            "ai_requests_per_day": 10,
            "storage_mb": 100,
            "api_calls_per_day": 50,
        },
        "starter": {
            "complaints_per_month": 250,
            "users": 5,
            "ai_requests_per_day": 100,
            "storage_mb": 1000,
            "api_calls_per_day": 500,
        },
        "professional": {
            "complaints_per_month": 1000,
            "users": 15,
            "ai_requests_per_day": 500,
            "storage_mb": 5000,
            "api_calls_per_day": 2000,
        },
        "enterprise": {
            "complaints_per_month": -1,  # Unlimited
            "users": -1,  # Unlimited
            "ai_requests_per_day": -1,  # Unlimited
            "storage_mb": -1,  # Unlimited
            "api_calls_per_day": -1,  # Unlimited
        },
    }

    return limits.get(plan_type.lower(), limits["free"])


def get_plan_price(plan_type: str) -> Decimal:
    """
    Get monthly price for subscription plan
    """
    prices = {
        "free": Decimal("0.00"),
        "starter": Decimal("99.00"),
        "professional": Decimal("299.00"),
        "enterprise": Decimal("799.00"),
    }

    return prices.get(plan_type.lower(), Decimal("0.00"))


def format_currency(amount: Decimal, currency: str = "TRY") -> str:
    """
    Format currency amount for display
    """
    if currency == "TRY":
        return f"₺{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def check_feature_access(organization, feature: str) -> bool:
    """
    Check if organization has access to specific feature
    """
    if not organization or not hasattr(organization, "subscription"):
        return False

    subscription = organization.subscription
    if not subscription or not subscription.is_active:
        return False

    plan_features = {
        "free": ["basic_complaints", "basic_reporting"],
        "starter": [
            "basic_complaints",
            "basic_reporting",
            "ai_sentiment",
            "email_notifications",
        ],
        "professional": [
            "basic_complaints",
            "basic_reporting",
            "ai_sentiment",
            "email_notifications",
            "advanced_analytics",
            "api_access",
            "custom_fields",
        ],
        "enterprise": [
            "basic_complaints",
            "basic_reporting",
            "ai_sentiment",
            "email_notifications",
            "advanced_analytics",
            "api_access",
            "custom_fields",
            "white_label",
            "priority_support",
            "custom_integrations",
        ],
    }

    plan_type = subscription.plan.plan_type.lower()
    allowed_features = plan_features.get(plan_type, [])

    return feature in allowed_features


def get_usage_percentage(current_usage: int, limit: int) -> float:
    """
    Calculate usage percentage
    """
    if limit == -1:  # Unlimited
        return 0.0

    if limit == 0:
        return 100.0

    return min((current_usage / limit) * 100, 100.0)


def is_usage_exceeded(current_usage: int, limit: int) -> bool:
    """
    Check if usage limit is exceeded
    """
    if limit == -1:  # Unlimited
        return False

    return current_usage >= limit


def get_next_billing_date(subscription):
    """
    Get next billing date for subscription
    """
    if not subscription:
        return None

    from datetime import datetime, timedelta

    if subscription.billing_cycle == "monthly":
        return subscription.current_period_end + timedelta(days=30)
    elif subscription.billing_cycle == "yearly":
        return subscription.current_period_end + timedelta(days=365)

    return subscription.current_period_end


def generate_invoice_number() -> str:
    """
    Generate unique invoice number
    """
    import random
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = random.randint(1000, 9999)

    return f"INV-{timestamp}-{random_suffix}"


def calculate_prorated_amount(plan_price: Decimal, days_remaining: int, total_days: int) -> Decimal:
    """
    Calculate prorated amount for plan changes
    """
    if total_days == 0:
        return Decimal("0.00")

    daily_rate = plan_price / total_days
    return daily_rate * days_remaining


def send_billing_notification(organization, notification_type: str, **kwargs):
    """
    Send billing-related notifications
    """
    # Placeholder for notification system
    logger.info(f"Billing notification sent to {organization.name}: {notification_type}")

    # In a real implementation, this would integrate with email/SMS services
    pass


def validate_subscription_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate subscription data
    """
    errors = {}

    required_fields = ["plan_type", "billing_cycle"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = f"{field} is required"

    valid_plans = ["free", "starter", "professional", "enterprise"]
    if data.get("plan_type") and data["plan_type"].lower() not in valid_plans:
        errors["plan_type"] = f"Invalid plan type. Must be one of: {', '.join(valid_plans)}"

    valid_cycles = ["monthly", "yearly"]
    if data.get("billing_cycle") and data["billing_cycle"].lower() not in valid_cycles:
        errors["billing_cycle"] = (
            f"Invalid billing cycle. Must be one of: {', '.join(valid_cycles)}"
        )

    return errors


def create_invoice(organization, amount: Decimal, description: str = "", **kwargs):
    """
    Create invoice for organization
    """
    from datetime import datetime

    from .models import Invoice

    invoice = Invoice.objects.create(
        organization=organization,
        invoice_number=generate_invoice_number(),
        amount=amount,
        description=description,
        due_date=datetime.now().date(),
        status="pending",
        **kwargs,
    )

    logger.info(f"Invoice created: {invoice.invoice_number} for {organization.name}")
    return invoice


def track_feature_usage(organization, feature: str, usage_count: int = 1):
    """
    Track feature usage for organization
    """
    from datetime import datetime

    from .models import FeatureUsage

    usage, created = FeatureUsage.objects.get_or_create(
        organization=organization,
        feature=feature,
        date=datetime.now().date(),
        defaults={"usage_count": 0},
    )

    usage.usage_count += usage_count
    usage.save()

    logger.info(f"Feature usage tracked: {feature} for {organization.name} (+{usage_count})")
    return usage
