"""
Solutio 360 Ana URL Yapılandırması
=================================

Bu dosya Solutio 360 PWA projesi için ana URL yapılandırmasını içerir.
Tüm uygulama modüllerinin URL'lerini birleştirir ve yönlendirir.

URL Yapısı:
- / - Ana sayfa
- /admin/ - Django admin paneli
- /accounts/ - Kullanıcı kimlik doğrulama (django-allauth)
- /complaints/ - Şikayet yönetimi
- /reports/ - Raporlama sistemi
- /users/ - Kullanıcı yönetimi
- /api/ - REST API endpoint'leri
- /dashboard/ - Yönetim paneli
- /swagger/ - API dokümantasyonu (Swagger UI)
- /redoc/ - API dokümantasyonu (ReDoc)

API Özellikleri:
- JWT token tabanlı kimlik doğrulama
- RESTful API tasarımı
- Swagger/OpenAPI dokümantasyonu
- CORS desteği

PWA Özellikleri:
- Service Worker desteği
- Offline sayfa
- Manifest dosyası
- Health check endpoint'i

Güvenlik:
- CSRF koruması
- XSS koruması
- SQL injection koruması
- Rate limiting

@author Solutio 360 Development Team
@version 1.0.0
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults
from django.views.generic import RedirectView, TemplateView

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from complaints.api import ComplaintViewSet
from core.views import dashboard
from reports.api import ReportViewSet

from .views import home

router = routers.DefaultRouter()
router.register(r"complaints", ComplaintViewSet)
router.register(r"reports", ReportViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="Solutio 360 API",
        default_version="v1",
        description="Şikayet ve Rapor Yönetim Sistemi API'si",
        terms_of_service="https://www.solutio360.com/terms/",
        contact=openapi.Contact(email="api@solutio360.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[],
)

urlpatterns = [
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("core/", include("core.urls", namespace="core")),
    path("complaints/", include("complaints.urls")),
    path("reports/", include("reports.urls")),
    path("users/", include("users.urls")),
    path("api/", include(router.urls)),
    path("api/", include("core.api_urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("dashboard/", dashboard, name="dashboard"),
    path("", include("pwa.urls")),
    path("health/", TemplateView.as_view(template_name="health.html"), name="health"),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),
    path("analytics/", include("analytics.urls")),
    path("saas/", include("saas_features.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [
        path(
            "400/",
            defaults.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            defaults.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            defaults.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", defaults.server_error),
        path("__debug__/", include("debug_toolbar.urls")),
    ]
