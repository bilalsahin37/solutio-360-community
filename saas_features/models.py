from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# from django_tenants.models import DomainMixin, TenantMixin  # Will be added when implementing full multi-tenancy


class Organization(
    models.Model
):  # Will inherit from TenantMixin when multi-tenancy is fully implemented
    """Multi-tenant organizasyon modeli"""

    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)

    # SaaS özellikleri
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ("free", "Free"),
            ("starter", "Starter"),
            ("professional", "Professional"),
            ("enterprise", "Enterprise"),
        ],
        default="free",
    )

    # Plan limitleri
    monthly_complaint_limit = models.IntegerField(default=25)
    user_limit = models.IntegerField(default=1)
    api_rate_limit = models.IntegerField(default=100)  # per day

    # Billing bilgileri
    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    # Subscription durumu
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("canceled", "Canceled"),
            ("suspended", "Suspended"),
        ],
        default="active",
    )

    subscription_start_date = models.DateTimeField(default=timezone.now)
    subscription_end_date = models.DateTimeField(null=True, blank=True)

    # Özelleştirme
    custom_domain = models.CharField(max_length=100, blank=True)
    custom_logo = models.ImageField(upload_to="tenant_logos/", blank=True)
    custom_colors = models.JSONField(default=dict, blank=True)

    # Kullanım istatistikleri
    current_month_complaints = models.IntegerField(default=0)
    total_users = models.IntegerField(default=0)

    auto_create_schema = True
    auto_drop_schema = True

    def __str__(self):
        return self.name

    def is_feature_enabled(self, feature_name):
        """Plan bazlı özellik kontrolü"""
        feature_matrix = {
            "free": {
                "advanced_ml": False,
                "real_time_analytics": False,
                "custom_branding": False,
                "api_access": False,
                "sso": False,
                "white_label": False,
                "custom_domain": False,
            },
            "starter": {
                "advanced_ml": False,
                "real_time_analytics": False,
                "custom_branding": False,
                "api_access": True,
                "sso": False,
                "white_label": False,
                "custom_domain": False,
            },
            "professional": {
                "advanced_ml": True,
                "real_time_analytics": True,
                "custom_branding": True,
                "api_access": True,
                "sso": False,
                "white_label": False,
                "custom_domain": False,
            },
            "enterprise": {
                "advanced_ml": True,
                "real_time_analytics": True,
                "custom_branding": True,
                "api_access": True,
                "sso": True,
                "white_label": True,
                "custom_domain": True,
            },
        }

        return feature_matrix.get(self.subscription_plan, {}).get(feature_name, False)

    def can_create_complaint(self):
        """Şikayet oluşturma limiti kontrolü"""
        return self.current_month_complaints < self.monthly_complaint_limit

    def can_add_user(self):
        """Kullanıcı ekleme limiti kontrolü"""
        return self.total_users < self.user_limit


class OrganizationDomain(
    models.Model
):  # Will inherit from DomainMixin when multi-tenancy is fully implemented
    """Tenant domain modeli"""

    domain = models.CharField(max_length=253, unique=True)
    tenant = models.ForeignKey(Organization, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=True)


class SubscriptionPlan(models.Model):
    """Abonelik planları"""

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)

    # Plan limitleri
    complaint_limit = models.IntegerField()
    user_limit = models.IntegerField()
    api_rate_limit = models.IntegerField()

    # Özellikler
    features = models.JSONField(default=dict)

    # Stripe bilgileri
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ₺{self.price_monthly}/ay"


class Subscription(models.Model):
    """Abonelik kayıtları"""

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)

    # Billing bilgileri
    billing_cycle = models.CharField(
        max_length=10,
        choices=[("monthly", "Monthly"), ("yearly", "Yearly")],
        default="monthly",
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("canceled", "Canceled"),
            ("trialing", "Trialing"),
        ],
        default="active",
    )

    # Tarihler
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)

    # Stripe bilgileri
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    # Otomatik yenileme
    auto_renew = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization.name} - {self.plan.name}"

    @property
    def is_active(self):
        """Abonelik aktif mi?"""
        return self.status == "active" and (
            not self.end_date or self.end_date > timezone.now()
        )

    @property
    def days_until_renewal(self):
        """Yenileme tarihine kaç gün kaldı?"""
        if self.end_date:
            return (self.end_date - timezone.now()).days
        return None


class Invoice(models.Model):
    """Fatura kayıtları"""

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    # Fatura bilgileri
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Durumlar
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
        ],
        default="draft",
    )

    # Tarihler
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)

    # Stripe bilgileri
    stripe_invoice_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - ₺{self.total_amount}"


class UsageTracking(models.Model):
    """Kullanım takibi"""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    # Kullanım metrikleri
    complaints_count = models.IntegerField(default=0)
    api_requests_count = models.IntegerField(default=0)
    active_users_count = models.IntegerField(default=0)

    # Tarih
    date = models.DateField(default=timezone.now)

    # ML kullanımı
    ml_predictions_count = models.IntegerField(default=0)
    sentiment_analysis_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["organization", "date"]

    def __str__(self):
        return f"{self.organization.name} - {self.date}"


class FeatureUsage(models.Model):
    """Özellik kullanım takibi"""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    feature_name = models.CharField(max_length=100)
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["organization", "feature_name"]

    def __str__(self):
        return f"{self.organization.name} - {self.feature_name}: {self.usage_count}"
