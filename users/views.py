"""
Kullanıcı Modülü View'ları
=========================

Bu dosya kullanıcı yönetimi için Django view'larını içerir.
Kullanıcı profilleri, listesi ve CRUD işlemleri için view'lar tanımlanmıştır.

View Türleri:
- ListView: Kullanıcı listesi
- DetailView: Kullanıcı detayları
- UpdateView: Kullanıcı güncelleme
- DeleteView: Kullanıcı silme

Güvenlik:
- LoginRequiredMixin: Giriş zorunluluğu
- UserPassesTestMixin: Yetki kontrolü
- Staff kontrolü admin işlemleri için
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from .models import User, UserProfile

# Create your views here.


class UserListView(LoginRequiredMixin, ListView):
    """
    Kullanıcı listesi view'ı.

    Sistemdeki tüm kullanıcıları listeler.
    Sadece giriş yapmış kullanıcılar erişebilir.

    Attributes:
        model: User modeli
        template_name: Kullanılacak template
        context_object_name: Template'de kullanılacak değişken adı
        ordering: Sıralama kriteri
    """

    model = User  # Kullanılacak model
    template_name = "users/user_list.html"  # Template dosyası
    context_object_name = "users"  # Template'de kullanılacak değişken
    ordering = ["username"]  # Kullanıcı adına göre alfabetik sıralama


class UserDetailView(LoginRequiredMixin, DetailView):
    """
    Kullanıcı detay view'ı.

    Belirli bir kullanıcının detay bilgilerini gösterir.
    Kullanıcı profili, istatistikler ve genel bilgiler.

    Attributes:
        model: User modeli
        template_name: Detay template'i
        context_object_name: Template değişken adı
    """

    model = User  # User modeli kullanılacak
    template_name = "users/user_detail.html"  # Detay template'i
    context_object_name = "user"  # Template'de 'user' değişkeni


class UserProfileView(LoginRequiredMixin, DetailView):
    """
    Kullanıcı profil view'ı.

    Giriş yapmış kullanıcının kendi profil sayfası.
    Kişisel bilgiler, ayarlar ve aktivite geçmişi.

    Methods:
        get_object(): Mevcut kullanıcıyı döndürür
        get_context_data(): Ek context verileri ekler
    """

    model = User  # User modeli
    template_name = "users/profile.html"  # Profil template'i
    context_object_name = "user"  # Template değişkeni

    def get_object(self):
        """
        Mevcut giriş yapmış kullanıcıyı döndürür.

        Returns:
            User: Giriş yapmış kullanıcı nesnesi
        """
        return self.request.user

    def get_context_data(self, **kwargs):
        """
        Template için ek context verileri ekler.

        Şikayet istatistiklerini hesaplar ve context'e ekler.

        Returns:
            dict: Template context verisi
        """
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        # Şikayet istatistiklerini hesapla (related_name="submitted_complaints" kullanılıyor)
        complaints = user.submitted_complaints.all()
        context["total_complaints"] = complaints.count()

        # Status'a göre şikayet sayıları
        context["pending_complaints"] = complaints.filter(status="SUBMITTED").count()
        context["resolved_complaints"] = complaints.filter(status="RESOLVED").count()
        context["in_progress_complaints"] = complaints.filter(status="IN_PROGRESS").count()
        context["draft_complaints"] = complaints.filter(status="DRAFT").count()
        context["in_review_complaints"] = complaints.filter(status="IN_REVIEW").count()

        return context


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Kullanıcı profil güncelleme view'ı.

    Kullanıcının kendi profil bilgilerini güncellemesi için form.
    Biyografi, telefon, departman, pozisyon ve avatar güncellenebilir.

    Attributes:
        model: UserProfile modeli
        fields: Güncellenebilir alanlar
        success_url: Başarılı güncelleme sonrası yönlendirme
    """

    model = UserProfile  # UserProfile modeli kullanılacak
    template_name = "users/profile_form.html"  # Form template'i

    # Güncellenebilir alanlar (UserProfile modelindeki alanlar)
    fields = [
        "birth_date",
        "gender",
        "address",
        "city",
        "country",
        "alternative_email",
        "alternative_phone",
        "linkedin",
        "twitter",
        "facebook",
        "instagram",
        "language",
        "timezone",
        "theme",
    ]

    # Başarılı güncelleme sonrası profil sayfasına yönlendir
    success_url = reverse_lazy("users:profile")

    def get_object(self):
        """
        Mevcut kullanıcının profil nesnesini döndürür.
        Profil yoksa otomatik oluşturur.

        Returns:
            UserProfile: Kullanıcının profil nesnesi
        """
        user = self.request.user
        try:
            return user.profile
        except UserProfile.DoesNotExist:
            # Profil yoksa otomatik oluştur
            return UserProfile.objects.create(user=user)


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Kullanıcı güncelleme view'ı (Admin).

    Sadece staff yetkisi olan kullanıcılar erişebilir.
    Diğer kullanıcıların temel bilgilerini günceller.

    Attributes:
        model: User modeli
        fields: Güncellenebilir alanlar
        success_url: Başarı sonrası yönlendirme

    Methods:
        test_func(): Yetki kontrolü
    """

    model = User  # User modeli
    template_name = "users/user_form.html"  # Form template'i

    # Admin tarafından güncellenebilir alanlar
    fields = ["username", "email", "first_name", "last_name", "is_active"]

    # Güncelleme sonrası kullanıcı listesine dön
    success_url = reverse_lazy("users:user_list")

    def test_func(self):
        """
        Yetki kontrolü - sadece staff kullanıcılar.

        Returns:
            bool: Kullanıcı staff ise True, değilse False
        """
        return self.request.user.is_staff


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Kullanıcı silme view'ı (Admin).

    Sadece staff yetkisi olan kullanıcılar erişebilir.
    Kullanıcı silme işlemi için onay sayfası gösterir.

    DİKKAT: Bu işlem geri alınamaz!

    Attributes:
        model: User modeli
        template_name: Onay template'i
        success_url: Silme sonrası yönlendirme

    Methods:
        test_func(): Yetki kontrolü
    """

    model = User  # User modeli
    template_name = "users/user_confirm_delete.html"  # Onay template'i

    # Silme sonrası kullanıcı listesine dön
    success_url = reverse_lazy("users:user_list")

    def test_func(self):
        """
        Yetki kontrolü - sadece staff kullanıcılar.

        Returns:
            bool: Kullanıcı staff ise True, değilse False
        """
        return self.request.user.is_staff


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    Özel şifre değiştirme view'ı.

    Django'nun varsayılan PasswordChangeView'ını özelleştirir.
    Kullanıcı şifresini güvenli şekilde değiştirebilir.

    Attributes:
        template_name: Şifre değiştirme form template'i
        success_url: Başarılı değişiklik sonrası yönlendirme
    """

    template_name = "users/password_change.html"  # Form template'i

    # Şifre değiştirme sonrası profil sayfasına yönlendir
    success_url = reverse_lazy("users:profile")


class UserSettingsView(LoginRequiredMixin, UpdateView):
    """
    Kullanıcı ayarları view'ı.

    Kullanıcının sistem ayarlarını güncelleme formu.
    Bildirim tercihleri, gizlilik ayarları vs.

    Attributes:
        model: User modeli
        template_name: Ayarlar template'i
        fields: Güncellenebilir ayar alanları
        success_url: Başarılı güncelleme sonrası yönlendirme
    """

    model = User
    template_name = "users/settings.html"
    fields = ["email", "first_name", "last_name"]
    success_url = reverse_lazy("users:settings")

    def get_object(self):
        """
        Mevcut kullanıcıyı döndürür.

        Returns:
            User: Giriş yapmış kullanıcı nesnesi
        """
        return self.request.user
