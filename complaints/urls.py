"""
Şikayet Modülü URL Yapılandırması
=================================

Bu dosya şikayet yönetim sistemi için URL rotalarını tanımlar.
Modern PWA uyumlu şikayet sistemi için tüm endpoint'leri içerir.

URL Yapısı:
- /complaints/ - Ana şikayet listesi
- /complaints/create/ - Yeni şikayet oluşturma
- /complaints/<uuid>/ - Şikayet detayı
- /complaints/<uuid>/update/ - Şikayet güncelleme
- /complaints/<uuid>/delete/ - Şikayet silme
- /complaints/reviewer-panel/ - İnceleme paneli
- /complaints/inspector-panel/ - Denetleme paneli
- /complaints/ajax/ - AJAX endpoint'leri

Güvenlik:
- Tüm view'lar login_required decorator ile korunmuştur
- CSRF koruması aktiftir
- Role-based access control uygulanmıştır
"""

from django.urls import path

from . import views
from .views import ajax_add_institution  # AJAX: Kurum ekleme
from .views import ajax_add_person  # AJAX: Kişi ekleme
from .views import ajax_add_subunit  # AJAX: Alt birim ekleme
from .views import ajax_add_tag  # AJAX: Etiket ekleme
from .views import ajax_add_unit  # AJAX: Birim ekleme
from .views import ajax_add_user  # AJAX: Kullanıcı ekleme
from .views import cancel_complaint  # Şikayet iptal etme
from .views import complaint_create  # Şikayet oluşturma
from .views import delete_complaint  # Şikayet silme
from .views import withdraw_complaint  # Şikayet geri çekme

# Uygulama namespace'i - URL tersine çevirmede kullanılır
app_name = "complaints"

# URL pattern'leri - Django'nun URL dispatcher'ı için
urlpatterns = [
    # Ana şikayet listesi - tüm şikayetleri görüntüler
    path("", views.ComplaintListView.as_view(), name="complaint_list"),
    # Yeni şikayet oluşturma formu
    path("create/", complaint_create, name="complaint_create"),
    # Şikayet detay sayfası - UUID ile erişim
    path("<uuid:pk>/", views.ComplaintDetailView.as_view(), name="complaint_detail"),
    # Şikayet güncelleme formu
    path(
        "<uuid:pk>/update/",
        views.ComplaintUpdateView.as_view(),
        name="complaint_update",
    ),
    # Şikayet silme onayı ve işlemi
    path(
        "<uuid:pk>/delete/",
        views.ComplaintDeleteView.as_view(),
        name="complaint_delete",
    ),
    # Şikayet geri çekme - kullanıcı kendi şikayetini geri çekebilir
    path("<uuid:pk>/withdraw/", withdraw_complaint, name="withdraw_complaint"),
    # Şikayet iptal etme - yönetici yetkisi gerekir
    path("<uuid:pk>/cancel/", cancel_complaint, name="cancel_complaint"),
    # Taslak şikayet silme - sadece taslak durumundaki şikayetler
    path("<uuid:pk>/delete-draft/", delete_complaint, name="delete_draft"),
    # Şikayete yorum ekleme
    path("<uuid:pk>/add_comment/", views.AddCommentView.as_view(), name="add_comment"),
    # Şikayet durumu güncelleme - yetkililer için
    path(
        "<uuid:pk>/update_status/",
        views.UpdateStatusView.as_view(),
        name="update_status",
    ),
    # İnceleme paneli - reviewer rolü için özel panel
    path(
        "reviewer-panel/",
        views.ReviewerComplaintListView.as_view(),
        name="reviewer_panel",
    ),
    # Denetleme paneli - inspector rolü için özel panel
    path(
        "inspector-panel/",
        views.InspectorComplaintListView.as_view(),
        name="inspector_panel",
    ),
    # AJAX Endpoint'leri - Dinamik form alanları için
    # Bu endpoint'ler modal formlardan çağrılır ve JSON response döner
    # Yeni kurum ekleme
    path("ajax/add-institution/", ajax_add_institution, name="ajax_add_institution"),
    # Yeni birim ekleme
    path("ajax/add-unit/", ajax_add_unit, name="ajax_add_unit"),
    # Yeni alt birim ekleme
    path("ajax/add-subunit/", ajax_add_subunit, name="ajax_add_subunit"),
    # Yeni kişi ekleme
    path("ajax/add-person/", ajax_add_person, name="ajax_add_person"),
    # Yeni etiket ekleme
    path("ajax/add-tag/", ajax_add_tag, name="ajax_add_tag"),
    # Yeni kullanıcı ekleme
    path("ajax/add-user/", ajax_add_user, name="ajax_add_user"),
    # Export işlemleri
    path("export/excel/", views.export_complaints_excel, name="export_excel"),
    path("export/pdf/", views.export_complaints_pdf, name="export_pdf"),
]
