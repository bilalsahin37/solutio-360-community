import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, TemplateView

import stripe

from .decorators import feature_required, usage_limit_check
from .models import (
    FeatureUsage,
    Invoice,
    Organization,
    Subscription,
    SubscriptionPlan,
    UsageTracking,
)
from .utils import create_invoice, track_feature_usage

# Stripe konfigürasyonu
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")


class SubscriptionDashboardView(TemplateView):
    """Abonelik yönetim dashboard'u"""

    template_name = "saas/subscription_dashboard.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Mevcut organizasyon ve abonelik bilgileri
        organization = self.request.tenant
        subscription = getattr(organization, "subscription", None)

        # Kullanım istatistikleri
        current_usage = UsageTracking.objects.filter(
            organization=organization, date=timezone.now().date()
        ).first()

        # Aylık kullanım trendi
        monthly_usage = UsageTracking.objects.filter(
            organization=organization,
            date__gte=timezone.now().date() - timedelta(days=30),
        ).order_by("date")

        # Tüm planlar
        available_plans = SubscriptionPlan.objects.filter(is_active=True)

        context.update(
            {
                "organization": organization,
                "subscription": subscription,
                "current_usage": current_usage,
                "monthly_usage": monthly_usage,
                "available_plans": available_plans,
                "current_plan": subscription.plan if subscription else None,
                "billing_info": self.get_billing_info(organization),
                "usage_stats": self.get_usage_stats(organization),
            }
        )

        return context

    def get_billing_info(self, organization):
        """Billing bilgileri"""
        subscription = getattr(organization, "subscription", None)
        if not subscription:
            return None

        # Son faturalar
        recent_invoices = Invoice.objects.filter(subscription=subscription).order_by("-created_at")[
            :5
        ]

        # Sonraki ödeme tarihi
        next_payment_date = subscription.end_date

        return {
            "next_payment_date": next_payment_date,
            "recent_invoices": recent_invoices,
            "billing_cycle": subscription.billing_cycle,
            "auto_renew": subscription.auto_renew,
        }

    def get_usage_stats(self, organization):
        """Kullanım istatistikleri"""
        # Bu ay kullanım
        current_month = timezone.now().replace(day=1)
        monthly_usage = UsageTracking.objects.filter(
            organization=organization, date__gte=current_month
        ).aggregate(
            total_complaints=models.Sum("complaints_count"),
            total_api_requests=models.Sum("api_requests_count"),
            total_ml_predictions=models.Sum("ml_predictions_count"),
        )

        # Limit yüzdeleri
        complaint_percentage = (
            (monthly_usage["total_complaints"] or 0) / organization.monthly_complaint_limit * 100
        )

        api_percentage = (
            (monthly_usage["total_api_requests"] or 0) / organization.api_rate_limit * 100
        )

        return {
            "complaints_used": monthly_usage["total_complaints"] or 0,
            "complaints_limit": organization.monthly_complaint_limit,
            "complaints_percentage": min(complaint_percentage, 100),
            "api_requests_used": monthly_usage["total_api_requests"] or 0,
            "api_requests_limit": organization.api_rate_limit,
            "api_requests_percentage": min(api_percentage, 100),
            "ml_predictions": monthly_usage["total_ml_predictions"] or 0,
        }


@login_required
def upgrade_plan(request, plan_id):
    """Plan yükseltme"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    organization = request.tenant
    new_plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    current_subscription = getattr(organization, "subscription", None)

    try:
        # Stripe checkout session oluştur
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": new_plan.stripe_price_id_monthly,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.build_absolute_uri("/saas/subscription/success/"),
            cancel_url=request.build_absolute_uri("/saas/subscription/cancel/"),
            client_reference_id=str(organization.id),
            metadata={
                "organization_id": organization.id,
                "plan_id": new_plan.id,
            },
        )

        return JsonResponse(
            {"checkout_url": checkout_session.url, "session_id": checkout_session.id}
        )

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def downgrade_plan(request, plan_id):
    """Plan düşürme"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    organization = request.tenant
    new_plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    current_subscription = getattr(organization, "subscription", None)

    if not current_subscription:
        return JsonResponse({"error": "No active subscription"}, status=400)

    try:
        # Stripe aboneliği güncelle
        stripe_subscription = stripe.Subscription.modify(
            current_subscription.stripe_subscription_id,
            items=[
                {
                    "id": current_subscription.stripe_subscription_id,
                    "price": new_plan.stripe_price_id_monthly,
                }
            ],
            proration_behavior="always_invoice",
        )

        # Veritabanını güncelle
        current_subscription.plan = new_plan
        current_subscription.save()

        # Organizasyon limitlerini güncelle
        organization.subscription_plan = new_plan.code
        organization.monthly_complaint_limit = new_plan.complaint_limit
        organization.user_limit = new_plan.user_limit
        organization.api_rate_limit = new_plan.api_rate_limit
        organization.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Plan successfully changed to {new_plan.name}",
            }
        )

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def stripe_webhook(request):
    """Stripe webhook handler"""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Event handling
    if event["type"] == "checkout.session.completed":
        handle_successful_payment(event["data"]["object"])
    elif event["type"] == "invoice.payment_succeeded":
        handle_successful_invoice_payment(event["data"]["object"])
    elif event["type"] == "invoice.payment_failed":
        handle_failed_invoice_payment(event["data"]["object"])
    elif event["type"] == "customer.subscription.deleted":
        handle_subscription_canceled(event["data"]["object"])

    return HttpResponse(status=200)


def handle_successful_payment(session):
    """Başarılı ödeme işlemi"""
    organization_id = session.get("client_reference_id")
    plan_id = session["metadata"].get("plan_id")

    if organization_id and plan_id:
        organization = Organization.objects.get(id=organization_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)

        # Abonelik oluştur veya güncelle
        subscription, created = Subscription.objects.get_or_create(
            organization=organization,
            defaults={
                "plan": plan,
                "stripe_subscription_id": session["subscription"],
                "stripe_customer_id": session["customer"],
                "status": "active",
                "start_date": timezone.now(),
                "end_date": timezone.now() + timedelta(days=30),
            },
        )

        if not created:
            subscription.plan = plan
            subscription.status = "active"
            subscription.save()

        # Organizasyon limitlerini güncelle
        organization.subscription_plan = plan.code
        organization.monthly_complaint_limit = plan.complaint_limit
        organization.user_limit = plan.user_limit
        organization.api_rate_limit = plan.api_rate_limit
        organization.subscription_status = "active"
        organization.save()

        # Hoş geldin emaili gönder
        send_welcome_email(organization, plan)


def handle_successful_invoice_payment(invoice):
    """Başarılı fatura ödemesi"""
    subscription_id = invoice["subscription"]

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)

        # Fatura kaydı oluştur
        create_invoice(
            subscription=subscription,
            stripe_invoice_id=invoice["id"],
            amount=invoice["amount_paid"] / 100,  # Cent to TL
            status="paid",
        )

        # Abonelik tarihini uzat
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.status = "active"
        subscription.save()

        # Organizasyon durumunu güncelle
        subscription.organization.subscription_status = "active"
        subscription.organization.save()

    except Subscription.DoesNotExist:
        pass


def handle_failed_invoice_payment(invoice):
    """Başarısız fatura ödemesi"""
    subscription_id = invoice["subscription"]

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)

        # Durumu güncelle
        subscription.status = "past_due"
        subscription.save()

        subscription.organization.subscription_status = "past_due"
        subscription.organization.save()

        # Uyarı emaili gönder
        send_payment_failed_email(subscription.organization)

    except Subscription.DoesNotExist:
        pass


def handle_subscription_canceled(subscription_data):
    """Abonelik iptal edildi"""
    subscription_id = subscription_data["id"]

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)

        subscription.status = "canceled"
        subscription.end_date = timezone.now()
        subscription.save()

        # Organizasyonu free plana düşür
        organization = subscription.organization
        organization.subscription_plan = "free"
        organization.monthly_complaint_limit = 25
        organization.user_limit = 1
        organization.api_rate_limit = 100
        organization.subscription_status = "canceled"
        organization.save()

        # İptal emaili gönder
        send_cancellation_email(organization)

    except Subscription.DoesNotExist:
        pass


def send_welcome_email(organization, plan):
    """Hoş geldin emaili"""
    subject = f"Solutio 360 {plan.name} Planına Hoş Geldiniz!"
    message = f"""
    Merhaba {organization.name},
    
    Solutio 360 {plan.name} planına başarıyla kaydoldunuz!
    
    Plan Özellikleri:
    - {plan.complaint_limit} şikayet/ay
    - {plan.user_limit} kullanıcı
    - API erişimi: {plan.api_rate_limit} istek/gün
    
    Dashboard'unuza erişmek için: https://{organization.custom_domain or 'app.solutio360.com'}
    
    Teşekkürler,
    Solutio 360 Ekibi
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [organization.billing_email],
        fail_silently=True,
    )


def send_payment_failed_email(organization):
    """Ödeme başarısız emaili"""
    subject = "Solutio 360 - Ödeme Hatası"
    message = f"""
    Merhaba {organization.name},
    
    Aboneliğinizin ödemesinde bir sorun oluştu.
    
    Lütfen ödeme bilgilerinizi güncelleyin: https://app.solutio360.com/billing/
    
    Sorularınız için bizimle iletişime geçin.
    
    Solutio 360 Ekibi
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [organization.billing_email],
        fail_silently=True,
    )


def send_cancellation_email(organization):
    """İptal emaili"""
    subject = "Solutio 360 - Abonelik İptal Edildi"
    message = f"""
    Merhaba {organization.name},
    
    Aboneliğiniz iptal edildi ve free plana geçildi.
    
    İstediğiniz zaman tekrar abone olabilirsiniz: https://app.solutio360.com/pricing/
    
    Geri dönüşlerinizi bekliyoruz.
    
    Solutio 360 Ekibi
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [organization.billing_email],
        fail_silently=True,
    )


@login_required
def usage_analytics(request):
    """Kullanım analitiği"""
    organization = request.tenant

    # Son 30 günün kullanımı
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    daily_usage = UsageTracking.objects.filter(
        organization=organization, date__gte=thirty_days_ago
    ).order_by("date")

    # Özellik kullanım istatistikleri
    feature_usage = FeatureUsage.objects.filter(organization=organization).order_by("-usage_count")[
        :10
    ]

    # API kullanım trendi
    api_usage_data = [usage.api_requests_count for usage in daily_usage]
    complaint_usage_data = [usage.complaints_count for usage in daily_usage]

    context = {
        "daily_usage": daily_usage,
        "feature_usage": feature_usage,
        "api_usage_data": api_usage_data,
        "complaint_usage_data": complaint_usage_data,
        "usage_dates": [usage.date.strftime("%Y-%m-%d") for usage in daily_usage],
    }

    return render(request, "saas/usage_analytics.html", context)


class PricingView(TemplateView):
    """Pricing sayfası"""

    template_name = "saas/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = SubscriptionPlan.objects.filter(is_active=True).order_by("price_monthly")
        return context


@login_required
def billing_dashboard(request):
    """Billing dashboard view"""
    organization = getattr(request, "tenant", None)
    if not organization:
        return render(request, "saas/billing_dashboard.html", {"error": "No organization found"})

    subscription = getattr(organization, "subscription", None)
    invoices = Invoice.objects.filter(organization=organization).order_by("-created_at")[:10]

    context = {
        "organization": organization,
        "subscription": subscription,
        "invoices": invoices,
        "total_cost": sum(inv.amount for inv in invoices if inv.status == "paid"),
    }

    return render(request, "saas/billing_dashboard.html", context)


@login_required
def invoice_list(request):
    """Invoice list view"""
    organization = getattr(request, "tenant", None)
    invoices = Invoice.objects.filter(organization=organization).order_by("-created_at")

    return render(request, "saas/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_detail(request, invoice_id):
    """Invoice detail view"""
    organization = getattr(request, "tenant", None)
    invoice = get_object_or_404(Invoice, id=invoice_id, organization=organization)

    return render(request, "saas/invoice_detail.html", {"invoice": invoice})


@login_required
def organization_settings(request):
    """Organization settings view"""
    organization = getattr(request, "tenant", None)

    return render(request, "saas/organization_settings.html", {"organization": organization})


@login_required
def organization_branding(request):
    """Organization branding view"""
    organization = getattr(request, "tenant", None)

    return render(request, "saas/organization_branding.html", {"organization": organization})


@login_required
def organization_users(request):
    """Organization users view"""
    organization = getattr(request, "tenant", None)
    users = organization.users.all() if organization else []

    return render(
        request,
        "saas/organization_users.html",
        {"users": users, "organization": organization},
    )


@login_required
def usage_data_api(request):
    """Usage data API endpoint"""
    organization = getattr(request, "tenant", None)
    if not organization:
        return JsonResponse({"error": "No organization found"}, status=400)

    usage_data = {
        "complaints_used": 0,
        "api_requests_used": 0,
        "storage_used": 0,
        "users_count": organization.users.count() if organization else 0,
    }

    return JsonResponse(usage_data)


@login_required
def create_subscription_api(request):
    """Create subscription API"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    return JsonResponse({"message": "Subscription creation not implemented yet"})


@login_required
def modify_subscription_api(request):
    """Modify subscription API"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    return JsonResponse({"message": "Subscription modification not implemented yet"})


@login_required
def current_usage_api(request):
    """Current usage API"""
    organization = getattr(request, "tenant", None)
    if not organization:
        return JsonResponse({"error": "No organization found"}, status=400)

    usage = {
        "complaints": 0,
        "api_requests": 0,
        "storage_mb": 0,
        "users": organization.users.count() if organization else 0,
    }

    return JsonResponse(usage)


@login_required
def check_feature_api(request, feature_name):
    """Check feature access API"""
    organization = getattr(request, "tenant", None)
    if not organization:
        return JsonResponse({"has_access": False, "error": "No organization found"})

    # Simple feature check - in real implementation would check subscription plan
    has_access = True  # Simplified for now

    return JsonResponse({"has_access": has_access, "feature": feature_name})


@login_required
def saas_onboarding(request):
    """SaaS onboarding view"""
    return render(request, "saas/onboarding.html")


@login_required
def complete_onboarding(request):
    """Complete onboarding process"""
    if request.method == "POST":
        # Process onboarding completion
        messages.success(request, "Onboarding completed successfully!")
        return redirect("saas:subscription_dashboard")

    return redirect("saas:onboarding")


@login_required
def cancel_subscription(request):
    """Abonelik iptal etme"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    organization = request.tenant
    subscription = getattr(organization, "subscription", None)

    if not subscription or subscription.status != "active":
        return JsonResponse({"error": "No active subscription to cancel"}, status=400)

    try:
        # Stripe aboneliği iptal et
        stripe.Subscription.delete(subscription.stripe_subscription_id)

        messages.success(request, "Aboneliğiniz başarıyla iptal edildi.")
        return JsonResponse({"success": True})

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)
