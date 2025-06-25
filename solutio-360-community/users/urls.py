"""
Kullanıcı Modülü URL Yapılandırması
==================================

Bu dosya kullanıcı yönetim sistemi için URL rotalarını tanımlar.
Kullanıcı profilleri, güncelleme ve yönetim işlemleri için endpoint'ler içerir.

URL Yapısı:
- /users/ - Kullanıcı listesi (admin için)
- /users/profile/ - Kendi profil sayfası
- /users/profile/update/ - Profil güncelleme
- /users/<id>/ - Kullanıcı detayı
- /users/<id>/update/ - Kullanıcı güncelleme (admin)
- /users/<id>/delete/ - Kullanıcı silme (admin)

Yetkilendirme:
- Tüm view'lar LoginRequiredMixin ile korunmuştur
- Admin işlemleri UserPassesTestMixin ile sınırlandırılmıştır
- Kullanıcılar sadece kendi profillerini düzenleyebilir
"""

from django.urls import path

from . import views

# Uygulama namespace'i - URL tersine çevirmede kullanılır
app_name = "users"

# URL pattern'leri - kullanıcı yönetimi için
urlpatterns = [
    # Kullanıcı listesi ve detayları
    path("", views.UserListView.as_view(), name="user_list"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    # Profil sayfaları
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("profile/edit/", views.UserProfileUpdateView.as_view(), name="profile_edit"),
    path("settings/", views.UserSettingsView.as_view(), name="settings"),
    # Admin işlemleri
    path("<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    path("<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    # Şifre değiştirme
    path("password/", views.CustomPasswordChangeView.as_view(), name="password_change"),
]
