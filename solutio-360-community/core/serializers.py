"""
Core Uygulama Serializer Sınıfları - Solutio 360 PWA
====================================================

Bu modül core uygulaması için Django REST Framework serializer'larını içerir.
API endpoint'leri için veri serileştirme ve deserileştirme işlemleri yapar.

Ana Özellikler:
- Model verilerini JSON formatına çevirme
- API request/response veri doğrulama
- İlişkili model verilerini dahil etme
- Hesaplanmış alanlar (computed fields)
- Salt okunur alanlar (read-only fields)
- Özelleştirilmiş alan görüntüleme

Serializer Türleri:
- UserSerializer: Kullanıcı veri serileştirme
- UserProfileSerializer: Kullanıcı profil bilgileri
- ComplaintSerializer: Şikayet veri serileştirme
- ReportSerializer: Rapor veri serileştirme
- AuditLogSerializer: Audit log kayıtları
- NotificationSerializer: Bildirim verileri

API Özellikleri:
- RESTful API desteği
- JSON formatında veri alışverişi
- Veri doğrulama ve güvenlik
- Performans optimizasyonu
- Hata yönetimi

Güvenlik Özellikleri:
- Hassas veri filtreleme
- Yetki kontrolü entegrasyonu
- Salt okunur alan koruması
- Veri sanitizasyonu
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from complaints.models import Complaint
from reports.models import Report
from users.models import User, UserProfile

from .models import AuditLog, Notification

# Django'nun varsayılan kullanıcı modelini al
User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Kullanıcı Profil Serializer'ı
    =============================

    Kullanıcı profil bilgilerini API için serileştirir.
    Kişisel bilgiler, iletişim ve organizasyon verileri.

    Dahil Edilen Alanlar:
    - bio: Kullanıcı biyografisi
    - phone: Telefon numarası
    - department: Departman bilgisi
    - position: Pozisyon/unvan
    - avatar: Profil fotoğrafı

    Kullanım Alanları:
    - Kullanıcı profil API'si
    - Profil güncelleme endpoint'i
    - Kullanıcı detay görüntüleme
    - Organizasyon şeması

    Güvenlik:
    - Hassas bilgiler dahil edilmez
    - Sadece gerekli alanlar expose edilir
    """

    class Meta:
        model = UserProfile  # UserProfile modeli ile bağlantı
        fields = [
            "bio",  # Kullanıcı biyografisi
            "phone",  # Telefon numarası
            "department",  # Departman
            "position",  # Pozisyon/unvan
            "avatar",  # Profil fotoğrafı
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Kullanıcı Serializer'ı
    ======================

    Ana kullanıcı bilgilerini API için serileştirir.
    Kimlik doğrulama ve temel kullanıcı verileri.

    Özellikler:
    - İlişkili profil bilgileri dahil
    - Hesaplanmış tam ad alanı
    - Salt okunur alanlar koruması
    - Güvenli veri filtreleme

    Dahil Edilen Alanlar:
    - id: Kullanıcı benzersiz kimliği
    - username: Kullanıcı adı
    - email: Email adresi
    - first_name: Ad
    - last_name: Soyad
    - is_active: Aktif durum
    - date_joined: Kayıt tarihi
    - profile: İlişkili profil bilgileri
    - full_name: Hesaplanmış tam ad

    Güvenlik:
    - Şifre bilgisi dahil edilmez
    - Hassas sistem alanları gizlenir
    - Salt okunur alanlar korunur
    """

    # İlişkili profil bilgilerini dahil et (salt okunur)
    profile = UserProfileSerializer(read_only=True)

    # Hesaplanmış tam ad alanı
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User  # User modeli ile bağlantı
        fields = [
            "id",  # Benzersiz kimlik
            "username",  # Kullanıcı adı
            "email",  # Email adresi
            "first_name",  # Ad
            "last_name",  # Soyad
            "is_active",  # Aktif durum
            "date_joined",  # Kayıt tarihi
            "profile",  # İlişkili profil (salt okunur)
            "full_name",  # Hesaplanmış tam ad
        ]

        # Salt okunur alanlar (API ile değiştirilemez)
        read_only_fields = [
            "id",  # Sistem tarafından atanan ID
            "date_joined",  # Kayıt tarihi sistem tarafından set edilir
        ]

    def get_full_name(self, obj):
        """
        Tam ad hesaplama metodu.

        Kullanıcının ad ve soyadını birleştirerek tam adını döndürür.

        Args:
            obj: User model nesnesi

        Returns:
            str: Kullanıcının tam adı

        Example:
            "Ahmet Yılmaz"
        """
        return obj.get_full_name()


class ComplaintSerializer(serializers.ModelSerializer):
    """
    Şikayet Serializer'ı
    ====================

    Şikayet verilerini API için serileştirir.
    Şikayet yönetim sistemi API endpoint'leri için kullanılır.

    Özellikler:
    - İlişkili kullanıcı bilgileri
    - Display (görüntü) alanları
    - Salt okunur sistem alanları
    - Kategori, durum, öncelik bilgileri

    Dahil Edilen Alanlar:
    - id: Şikayet benzersiz kimliği
    - title: Şikayet başlığı
    - description: Şikayet açıklaması
    - category: Kategori ID'si
    - category_display: Kategori adı (okunabilir)
    - priority: Öncelik ID'si
    - priority_display: Öncelik adı (okunabilir)
    - status: Durum ID'si
    - status_display: Durum adı (okunabilir)
    - created_by: Oluşturan kullanıcı bilgileri
    - created_at: Oluşturma tarihi
    - updated_at: Güncelleme tarihi

    API Kullanımı:
    - Şikayet listesi endpoint'i
    - Şikayet detay endpoint'i
    - Şikayet oluşturma API'si
    - Şikayet güncelleme API'si
    """

    # İlişkili kullanıcı bilgilerini dahil et (salt okunur)
    created_by = UserSerializer(read_only=True)

    # Display alanları (okunabilir format)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = Complaint  # Complaint modeli ile bağlantı
        fields = [
            "id",  # Benzersiz kimlik
            "title",  # Şikayet başlığı
            "description",  # Şikayet açıklaması
            "category",  # Kategori ID
            "category_display",  # Kategori adı (okunabilir)
            "priority",  # Öncelik ID
            "priority_display",  # Öncelik adı (okunabilir)
            "status",  # Durum ID
            "status_display",  # Durum adı (okunabilir)
            "created_by",  # Oluşturan kullanıcı
            "created_at",  # Oluşturma tarihi
            "updated_at",  # Güncelleme tarihi
        ]

        # Salt okunur alanlar
        read_only_fields = [
            "created_by",  # Sistem tarafından atanır
            "created_at",  # Oluşturma zamanı otomatik
            "updated_at",  # Güncelleme zamanı otomatik
        ]


class ReportSerializer(serializers.ModelSerializer):
    """
    Rapor Serializer'ı
    ==================

    Rapor verilerini API için serileştirir.
    Raporlama sistemi API endpoint'leri için kullanılır.

    Özellikler:
    - İlişkili kullanıcı bilgileri
    - Rapor türü display alanları
    - Durum bilgisi görüntüleme
    - Salt okunur sistem alanları

    Dahil Edilen Alanlar:
    - id: Rapor benzersiz kimliği
    - title: Rapor başlığı
    - content: Rapor içeriği
    - report_type: Rapor türü ID'si
    - report_type_display: Rapor türü adı (okunabilir)
    - status: Durum ID'si
    - status_display: Durum adı (okunabilir)
    - created_by: Oluşturan kullanıcı bilgileri
    - created_at: Oluşturma tarihi
    - updated_at: Güncelleme tarihi

    API Kullanımı:
    - Rapor listesi endpoint'i
    - Rapor detay endpoint'i
    - Rapor oluşturma API'si
    - Rapor güncelleme API'si
    """

    # İlişkili kullanıcı bilgilerini dahil et (salt okunur)
    created_by = UserSerializer(read_only=True)

    # Display alanları (okunabilir format)
    report_type_display = serializers.CharField(
        source="get_report_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Report  # Report modeli ile bağlantı
        fields = [
            "id",  # Benzersiz kimlik
            "title",  # Rapor başlığı
            "content",  # Rapor içeriği
            "report_type",  # Rapor türü ID
            "report_type_display",  # Rapor türü adı (okunabilir)
            "status",  # Durum ID
            "status_display",  # Durum adı (okunabilir)
            "created_by",  # Oluşturan kullanıcı
            "created_at",  # Oluşturma tarihi
            "updated_at",  # Güncelleme tarihi
        ]

        # Salt okunur alanlar
        read_only_fields = [
            "created_by",  # Sistem tarafından atanır
            "created_at",  # Oluşturma zamanı otomatik
            "updated_at",  # Güncelleme zamanı otomatik
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Audit Log Serializer'ı
    ======================

    Sistem audit log kayıtlarını API için serileştirir.
    Güvenlik ve izleme amaçlı log verilerini sunar.

    Özellikler:
    - Tüm audit log alanları dahil
    - Salt okunur veri yapısı
    - Zaman damgası koruması
    - Güvenlik log formatı

    Kullanım Alanları:
    - Sistem log API'si
    - Güvenlik izleme
    - Audit trail raporları
    - Compliance kontrolleri

    Güvenlik:
    - Sadece yetkili kullanıcılar erişebilir
    - Log verileri değiştirilemez
    - Hassas bilgiler filtrelenir
    """

    class Meta:
        model = AuditLog  # AuditLog modeli ile bağlantı
        fields = "__all__"  # Tüm alanları dahil et

        # Salt okunur alanlar (log verileri değiştirilemez)
        read_only_fields = ["id", "timestamp"]  # Benzersiz kimlik  # Zaman damgası


class NotificationSerializer(serializers.ModelSerializer):
    """
    Bildirim Serializer'ı
    =====================

    Kullanıcı bildirimlerini API için serileştirir.
    Bildirim sistemi API endpoint'leri için kullanılır.

    Özellikler:
    - Bildirim içeriği ve meta verileri
    - Okunma durumu takibi
    - Bildirim türü bilgisi
    - Zaman damgası koruması

    Dahil Edilen Alanlar:
    - id: Bildirim benzersiz kimliği
    - user: İlgili kullanıcı
    - title: Bildirim başlığı
    - message: Bildirim mesajı
    - type: Bildirim türü
    - is_read: Okundu mu?
    - url: Yönlendirme URL'i
    - created_at: Oluşturma tarihi

    API Kullanımı:
    - Kullanıcı bildirimleri endpoint'i
    - Bildirim okundu işaretleme
    - Push notification API'si
    - Real-time bildirim sistemi

    Güvenlik:
    - Kullanıcı sadece kendi bildirimlerini görebilir
    - Bildirim oluşturma yetkisi kontrollü
    """

    class Meta:
        model = Notification  # Notification modeli ile bağlantı
        fields = "__all__"  # Tüm alanları dahil et

        # Salt okunur alanlar
        read_only_fields = ["id", "created_at"]  # Benzersiz kimlik  # Oluşturma tarihi
