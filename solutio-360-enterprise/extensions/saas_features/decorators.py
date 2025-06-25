from functools import wraps

from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import FeatureUsage, Organization, UsageTracking


def feature_required(feature_name, redirect_to="saas:upgrade"):
    """
    Plan bazlı özellik kontrolü decorator'ı

    Usage:
        @feature_required('advanced_ml')
        def my_view(request):
            pass
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Multi-tenant organizasyon kontrolü
            organization = getattr(request, "tenant", None)
            if not organization:
                return HttpResponseForbidden("Organization not found")

            # Özellik kontrol et
            if not organization.is_feature_enabled(feature_name):
                # AJAX isteği ise JSON response
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "error": f"Bu özellik {organization.subscription_plan} planında mevcut değil",
                            "feature": feature_name,
                            "current_plan": organization.subscription_plan,
                            "upgrade_required": True,
                        },
                        status=403,
                    )

                # Normal istek ise upgrade sayfasına yönlendir
                messages.warning(
                    request,
                    f"Bu özellik {organization.get_subscription_plan_display()} planında mevcut değil. Lütfen planınızı yükseltiniz.",
                )
                return redirect(redirect_to)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def usage_limit_check(usage_type, limit_field):
    """
    Kullanım limiti kontrolü decorator'ı

    Usage:
        @usage_limit_check('complaints', 'monthly_complaint_limit')
        def create_complaint(request):
            pass
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            organization = getattr(request, "tenant", None)
            if not organization:
                return HttpResponseForbidden("Organization not found")

            # Mevcut kullanımı kontrol et
            current_usage = get_current_usage(organization, usage_type)
            limit = getattr(organization, limit_field, 0)

            if current_usage >= limit:
                # Kullanım limiti aşıldı
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "error": f"{usage_type} limitiniz doldu",
                            "current_usage": current_usage,
                            "limit": limit,
                            "upgrade_required": True,
                        },
                        status=429,
                    )

                messages.error(
                    request,
                    f"{usage_type.title()} limitiniz doldu. Planınızı yükseltmeniz gerekiyor.",
                )
                return redirect("saas:upgrade")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def track_feature_usage(feature_name):
    """
    Özellik kullanımını takip eden decorator

    Usage:
        @track_feature_usage('sentiment_analysis')
        def analyze_sentiment(request):
            pass
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            organization = getattr(request, "tenant", None)

            # View'ı çalıştır
            response = view_func(request, *args, **kwargs)

            # Başarılı response ise kullanımı kaydet
            if (
                organization
                and hasattr(response, "status_code")
                and response.status_code == 200
            ):
                feature_usage, created = FeatureUsage.objects.get_or_create(
                    organization=organization,
                    feature_name=feature_name,
                    defaults={"usage_count": 0},
                )
                feature_usage.usage_count += 1
                feature_usage.save()

                # Günlük kullanım tracking'i güncelle
                today = timezone.now().date()
                daily_usage, created = UsageTracking.objects.get_or_create(
                    organization=organization,
                    date=today,
                    defaults={
                        "complaints_count": 0,
                        "api_requests_count": 0,
                        "active_users_count": 0,
                        "ml_predictions_count": 0,
                        "sentiment_analysis_count": 0,
                    },
                )

                # Feature bazlı counting
                if feature_name == "sentiment_analysis":
                    daily_usage.sentiment_analysis_count += 1
                elif feature_name in ["ml_prediction", "category_prediction"]:
                    daily_usage.ml_predictions_count += 1
                elif feature_name == "api_request":
                    daily_usage.api_requests_count += 1

                daily_usage.save()

            return response

        return wrapper

    return decorator


def subscription_required(redirect_to="saas:subscription"):
    """
    Aktif abonelik kontrolü decorator'ı
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            organization = getattr(request, "tenant", None)
            if not organization:
                return HttpResponseForbidden("Organization not found")

            # Abonelik durumu kontrol et
            if organization.subscription_status not in ["active", "trialing"]:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "error": "Aktif abonelik gerekli",
                            "subscription_status": organization.subscription_status,
                        },
                        status=403,
                    )

                messages.warning(
                    request, "Bu özelliği kullanmak için aktif abonelik gereklidir."
                )
                return redirect(redirect_to)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def admin_required(view_func):
    """
    Organizasyon admin yetkisi kontrolü
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        # Kullanıcının organizasyon admin yetkisi var mı?
        if not hasattr(request.user, "role") or not request.user.role.is_admin:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": "Admin yetkisi gerekli"}, status=403)

            messages.error(request, "Bu işlem için admin yetkisi gereklidir.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


def rate_limit(requests_per_minute=60):
    """
    API rate limiting decorator'ı
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            organization = getattr(request, "tenant", None)
            if not organization:
                return HttpResponseForbidden("Organization not found")

            # Redis kullanılabilir ise rate limiting uygula
            try:
                import redis

                r = redis.Redis(host="localhost", port=6379, db=0)

                # Rate limit key
                key = f"rate_limit:{organization.id}:{timezone.now().strftime('%Y-%m-%d-%H-%M')}"

                # Mevcut istek sayısı
                current_requests = r.get(key)
                if current_requests is None:
                    r.setex(key, 60, 1)  # 60 saniye TTL
                else:
                    current_requests = int(current_requests)
                    if current_requests >= requests_per_minute:
                        return JsonResponse(
                            {
                                "error": "Rate limit exceeded",
                                "limit": requests_per_minute,
                                "reset_in_seconds": 60,
                            },
                            status=429,
                        )

                    r.incr(key)

            except ImportError:
                # Redis yoksa basit rate limiting (memory-based)
                pass

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def get_current_usage(organization, usage_type):
    """Mevcut kullanım miktarını getir"""
    today = timezone.now().date()
    current_month = today.replace(day=1)

    # Bu ayın toplam kullanımı
    monthly_usage = UsageTracking.objects.filter(
        organization=organization, date__gte=current_month
    ).aggregate(
        total_complaints=models.Sum("complaints_count"),
        total_api_requests=models.Sum("api_requests_count"),
        total_ml_predictions=models.Sum("ml_predictions_count"),
    )

    usage_map = {
        "complaints": monthly_usage.get("total_complaints", 0) or 0,
        "api_requests": monthly_usage.get("total_api_requests", 0) or 0,
        "ml_predictions": monthly_usage.get("total_ml_predictions", 0) or 0,
    }

    return usage_map.get(usage_type, 0)


# Kullanım örneği için helper fonksiyonlar
def increment_usage(organization, usage_type, amount=1):
    """Kullanım sayacını artır"""
    today = timezone.now().date()
    daily_usage, created = UsageTracking.objects.get_or_create(
        organization=organization,
        date=today,
        defaults={
            "complaints_count": 0,
            "api_requests_count": 0,
            "active_users_count": 0,
            "ml_predictions_count": 0,
            "sentiment_analysis_count": 0,
        },
    )

    if usage_type == "complaints":
        daily_usage.complaints_count += amount
        organization.current_month_complaints += amount
        organization.save()
    elif usage_type == "api_requests":
        daily_usage.api_requests_count += amount
    elif usage_type == "ml_predictions":
        daily_usage.ml_predictions_count += amount

    daily_usage.save()


def check_plan_limits(organization):
    """Plan limitlerini kontrol et ve uyarı ver"""
    warnings = []

    # Şikayet limiti kontrolü
    complaint_usage = get_current_usage(organization, "complaints")
    complaint_percentage = (
        complaint_usage / organization.monthly_complaint_limit
    ) * 100

    if complaint_percentage >= 90:
        warnings.append(
            {
                "type": "complaints",
                "message": f"Aylık şikayet limitinizin %{complaint_percentage:.0f}ını kullandınız",
                "severity": "critical" if complaint_percentage >= 95 else "warning",
            }
        )

    # API limiti kontrolü
    api_usage = get_current_usage(organization, "api_requests")
    api_percentage = (api_usage / organization.api_rate_limit) * 100

    if api_percentage >= 90:
        warnings.append(
            {
                "type": "api",
                "message": f"Günlük API limitinizin %{api_percentage:.0f}ını kullandınız",
                "severity": "critical" if api_percentage >= 95 else "warning",
            }
        )

    return warnings
