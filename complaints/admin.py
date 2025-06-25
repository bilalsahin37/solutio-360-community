"""
Şikayet Yönetimi Django Admin Konfigürasyonu - Solutio 360 PWA
==============================================================

Bu modül şikayet sistemi için Django Admin paneli konfigürasyonlarını içerir.
Yönetici arayüzünde kolay ve etkili veri yönetimi sağlar.

Ana Özellikler:
- Şikayet yönetimi admin paneli
- Kategori ve etiket yönetimi
- Yorum sistemi yönetimi
- Dosya eki yönetimi
- Gelişmiş filtreleme ve arama
- Toplu işlemler
- Özelleştirilmiş alan görünümleri

Admin Sınıfları:
- ComplaintAdmin: Ana şikayet yönetimi
- ComplaintCommentAdmin: Yorum yönetimi
- ComplaintTagAdmin: Etiket yönetimi
- ComplaintAttachmentAdmin: Dosya eki yönetimi

Özellikler:
- Liste görünümü optimizasyonu
- Arama ve filtreleme
- Salt okunur alanlar
- Fieldset organizasyonu
- İlişkili model erişimi
"""

from django.contrib import admin

from .models import (
    Complaint,
    ComplaintAttachment,
    ComplaintCategory,
    ComplaintComment,
    ComplaintTag,
    Institution,
    Person,
    Priority,
    Status,
    Subunit,
    Unit,
)

# Register your models here.


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """
    Şikayet Admin Sınıfı
    ===================

    Ana şikayet yönetimi için Django admin konfigürasyonu.
    Şikayetlerin listelenmesi, düzenlenmesi ve yönetimi.

    Özellikler:
    - Detaylı liste görünümü
    - Gelişmiş arama sistemi
    - Çoklu filtreleme seçenekleri
    - Fieldset ile organize edilmiş form
    - Salt okunur alanlar
    - İlişkili model erişimi

    Liste Görünümü:
    - Başlık, kategori, durum, öncelik
    - Şikayet sahibi ve atanan kişi
    - Oluşturma tarihi

    Filtreleme:
    - Durum, öncelik, kategori bazında

    Arama:
    - Başlık ve açıklama metinlerinde
    """

    # Liste görünümünde gösterilecek alanlar
    list_display = (
        "title",  # Şikayet başlığı
        "category",  # Kategori
        "status",  # Durum
        "priority",  # Öncelik
        "submitter",  # Şikayet sahibi
        "assigned_to",  # Atanan kişi
        "created_at",  # Oluşturma tarihi
    )

    # Arama yapılabilecek alanlar
    search_fields = (
        "title",  # Başlık alanında arama
        "description",  # Açıklama alanında arama
    )

    # Filtreleme seçenekleri (sağ panel)
    list_filter = (
        "status",  # Durum filtresi
        "priority",  # Öncelik filtresi
        "category",  # Kategori filtresi
    )

    # Salt okunur alanlar (düzenlenemez)
    # readonly_fields = ("ml_analysis",)  # Makine öğrenmesi analiz sonucu - Temporarily disabled

    # Form alanlarının organize edilmesi (fieldset)
    fieldsets = (
        # Ana Bilgiler Bölümü
        (
            None,  # Başlık yok
            {
                "fields": (
                    "title",  # Şikayet başlığı
                    "category",  # Kategori
                    "status",  # Durum
                    "priority",  # Öncelik
                    "submitter",  # Şikayet sahibi
                    "assigned_to",  # Atanan kişi
                    "department",  # Departman
                    "due_date",  # Bitiş tarihi
                    "is_anonymous",  # Anonim mi?
                    "is_confidential",  # Gizli mi?
                    "tags",  # Etiketler
                    # "ml_analysis",  # ML analizi (salt okunur) - Temporarily disabled
                )
            },
        ),
        # Çözüm Bilgileri Bölümü
        (
            "Çözüm",  # Bölüm başlığı
            {
                "fields": (
                    "resolution",  # Çözüm açıklaması
                    "resolution_date",  # Çözüm tarihi
                    "satisfaction_rating",  # Memnuniyet puanı
                    "satisfaction_comment",  # Memnuniyet yorumu
                )
            },
        ),
    )

    def get_queryset(self, request):
        """
        Admin liste sorgusu optimizasyonu.

        İlişkili modelleri tek sorguda getirir (select_related).
        Performans optimizasyonu sağlar.

        Args:
            request: HTTP request nesnesi

        Returns:
            QuerySet: Optimize edilmiş şikayet listesi
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "category",  # Kategori bilgilerini getir
            "status",  # Durum bilgilerini getir
            "priority",  # Öncelik bilgilerini getir
            "submitter",  # Şikayet sahibi bilgilerini getir
            "assigned_to",  # Atanan kişi bilgilerini getir
        )

    def get_readonly_fields(self, request, obj=None):
        """
        Dinamik salt okunur alanlar.

        Kullanıcı yetkisine göre salt okunur alanları belirler.

        Args:
            request: HTTP request nesnesi
            obj: Düzenlenen nesne (None ise yeni kayıt)

        Returns:
            tuple: Salt okunur alan listesi
        """
        readonly = list(self.readonly_fields)

        # Süper admin değilse bazı alanları salt okunur yap
        if not request.user.is_superuser:
            readonly.extend(
                [
                    "submitter",  # Şikayet sahibini değiştiremesin
                    "created_at",  # Oluşturma tarihini değiştiremesin
                ]
            )

        return readonly

    def has_delete_permission(self, request, obj=None):
        """
        Silme yetkisi kontrolü.

        Sadece süper adminler şikayetleri silebilir.

        Args:
            request: HTTP request nesnesi
            obj: Silinecek nesne

        Returns:
            bool: Silme yetkisi var mı?
        """
        return request.user.is_superuser


# Kategori modeli için basit admin kaydı
admin.site.register(ComplaintCategory)

# Öncelik modeli için basit admin kaydı
admin.site.register(Priority)

# Durum modeli için basit admin kaydı
admin.site.register(Status)


@admin.register(ComplaintComment)
class ComplaintCommentAdmin(admin.ModelAdmin):
    """
    Şikayet Yorumu Admin Sınıfı
    ===========================

    Şikayet yorumları için Django admin konfigürasyonu.
    Yorum yönetimi ve moderasyon işlemleri.

    Özellikler:
    - Yorum listesi görünümü
    - İçerik bazlı arama
    - Dahili/harici yorum filtresi
    - Şikayet ile ilişki görünümü
    - Gönderen ve alıcı bilgileri

    Liste Görünümü:
    - İlgili şikayet
    - Yorum içeriği (kısaltılmış)
    - Gönderen ve alıcı
    - Oluşturma tarihi

    Filtreleme:
    - Dahili yorum mu?
    - Oluşturma tarihi

    Arama:
    - Yorum içeriğinde
    """

    # Liste görünümünde gösterilecek alanlar
    list_display = (
        "complaint",  # İlgili şikayet
        "content",  # Yorum içeriği
        "sender",  # Gönderen
        "receiver",  # Alıcı
        "created_at",  # Oluşturma tarihi
    )

    # Arama yapılabilecek alanlar
    search_fields = ("content",)  # Yorum içeriğinde arama

    # Filtreleme seçenekleri
    list_filter = (
        "is_internal",  # Dahili yorum filtresi
        "created_at",  # Tarih filtresi
    )

    def get_queryset(self, request):
        """
        Yorum liste sorgusu optimizasyonu.

        İlişkili modelleri tek sorguda getirir.

        Args:
            request: HTTP request nesnesi

        Returns:
            QuerySet: Optimize edilmiş yorum listesi
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "complaint",  # Şikayet bilgilerini getir
            "sender",  # Gönderen bilgilerini getir
            "receiver",  # Alıcı bilgilerini getir
        )

    def content_short(self, obj):
        """
        Kısaltılmış yorum içeriği.

        Liste görünümünde uzun yorumları kısaltır.

        Args:
            obj: ComplaintComment nesnesi

        Returns:
            str: Kısaltılmış içerik
        """
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content

    # Kısaltılmış içerik için kolon başlığı
    content_short.short_description = "İçerik (Kısa)"


@admin.register(ComplaintTag)
class ComplaintTagAdmin(admin.ModelAdmin):
    """
    Şikayet Etiketi Admin Sınıfı
    ============================

    Şikayet etiketleri için Django admin konfigürasyonu.
    Etiket yönetimi ve renk düzenlemeleri.

    Özellikler:
    - Etiket listesi görünümü
    - Ad bazlı arama
    - Renk ve açıklama yönetimi
    - Kullanım istatistikleri

    Liste Görünümü:
    - Etiket adı
    - Renk kodu
    - Açıklama

    Arama:
    - Etiket adında
    """

    # Liste görünümünde gösterilecek alanlar
    list_display = (
        "name",  # Etiket adı
        "color",  # Renk kodu
        "description",  # Açıklama
    )

    # Arama yapılabilecek alanlar
    search_fields = ("name",)  # Etiket adında arama

    def get_queryset(self, request):
        """
        Etiket liste sorgusu.

        Etiket kullanım sayısı ile birlikte getirir.

        Args:
            request: HTTP request nesnesi

        Returns:
            QuerySet: Etiket listesi
        """
        from django.db.models import Count

        queryset = super().get_queryset(request)
        return queryset.annotate(
            usage_count=Count("complaint")  # Kaç şikayette kullanıldığını say
        )

    def usage_count(self, obj):
        """
        Etiket kullanım sayısı.

        Bu etiketin kaç şikayette kullanıldığını gösterir.

        Args:
            obj: ComplaintTag nesnesi

        Returns:
            int: Kullanım sayısı
        """
        return obj.usage_count if hasattr(obj, "usage_count") else 0

    # Kullanım sayısı için kolon başlığı
    usage_count.short_description = "Kullanım Sayısı"


# Kurum modeli için basit admin kaydı
admin.site.register(Institution)

# Birim modeli için basit admin kaydı
admin.site.register(Unit)

# Alt birim modeli için basit admin kaydı
admin.site.register(Subunit)

# Kişi modeli için basit admin kaydı
admin.site.register(Person)


@admin.register(ComplaintAttachment)
class ComplaintAttachmentAdmin(admin.ModelAdmin):
    """
    Şikayet Eki Admin Sınıfı
    ========================

    Şikayet dosya ekleri için Django admin konfigürasyonu.
    Dosya yönetimi ve güvenlik kontrolleri.

    Özellikler:
    - Dosya listesi görünümü
    - Dosya adı bazlı arama
    - Dosya türü ve boyut bilgileri
    - İlgili şikayet erişimi
    - Güvenlik kontrolleri

    Liste Görünümü:
    - İlgili şikayet
    - Dosya adı
    - Dosya türü
    - Dosya boyutu
    - Yükleme tarihi

    Arama:
    - Dosya adında
    """

    # Liste görünümünde gösterilecek alanlar
    list_display = (
        "complaint",  # İlgili şikayet
        "filename",  # Dosya adı
        "file_type",  # Dosya türü (MIME)
        "file_size",  # Dosya boyutu
        "created_at",  # Yükleme tarihi
    )

    # Arama yapılabilecek alanlar
    search_fields = ("filename",)  # Dosya adında arama

    def get_queryset(self, request):
        """
        Dosya eki liste sorgusu optimizasyonu.

        İlişkili şikayet bilgilerini tek sorguda getirir.

        Args:
            request: HTTP request nesnesi

        Returns:
            QuerySet: Optimize edilmiş dosya listesi
        """
        queryset = super().get_queryset(request)
        return queryset.select_related("complaint")

    def file_size_formatted(self, obj):
        """
        Formatlanmış dosya boyutu.

        Dosya boyutunu okunabilir formatta gösterir.

        Args:
            obj: ComplaintAttachment nesnesi

        Returns:
            str: Formatlanmış boyut (KB, MB, GB)
        """
        if not obj.file_size:
            return "Bilinmiyor"

        size = obj.file_size

        # Byte cinsinden boyutu uygun birime çevir
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    # Formatlanmış boyut için kolon başlığı
    file_size_formatted.short_description = "Dosya Boyutu"

    def has_change_permission(self, request, obj=None):
        """
        Değiştirme yetkisi kontrolü.

        Dosya ekleri genellikle değiştirilmemelidir.
        Sadece süper adminler değiştirebilir.

        Args:
            request: HTTP request nesnesi
            obj: Değiştirilecek nesne

        Returns:
            bool: Değiştirme yetkisi var mı?
        """
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """
        Silme yetkisi kontrolü.

        Dosya silme işlemi dikkatli yapılmalıdır.
        Sadece süper adminler silebilir.

        Args:
            request: HTTP request nesnesi
            obj: Silinecek nesne

        Returns:
            bool: Silme yetkisi var mı?
        """
        return request.user.is_superuser


# Admin site başlık ve açıklama özelleştirmeleri
admin.site.site_header = "Solutio 360 PWA - Şikayet Yönetimi"  # Başlık
admin.site.site_title = "Solutio 360 Admin"  # Tarayıcı başlığı
admin.site.index_title = "Şikayet Yönetim Paneli"  # Ana sayfa başlığı
