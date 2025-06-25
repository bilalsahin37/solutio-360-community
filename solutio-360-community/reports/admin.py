"""
Raporlama Sistemi Django Admin Konfigürasyonu - Solutio 360 PWA
===============================================================

Bu modül raporlama sistemi için Django Admin paneli konfigürasyonlarını içerir.
Rapor yönetimi, şablon düzenleme ve raporlama analizi için yönetici arayüzü sağlar.

Ana Özellikler:
- Rapor yönetimi admin paneli
- Rapor türü ve format yönetimi
- Departman bazlı filtreleme
- Makine öğrenmesi analiz sonuçları
- Gelişmiş arama ve filtreleme
- Rapor şablonu yönetimi

Admin Sınıfları:
- ReportAdmin: Ana rapor yönetimi

Özellikler:
- Liste görünümü optimizasyonu
- Arama ve filtreleme sistemi
- Salt okunur alanlar
- Fieldset organizasyonu
- İlişkili model erişimi
- Performans optimizasyonu

Güvenlik:
- Yetki tabanlı erişim kontrolü
- Hassas veri koruması
- Güvenli dosya yükleme
"""

from django.contrib import admin

from .models import Report

# Register your models here.


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Rapor Admin Sınıfı
    ==================

    Raporlama sistemi için Django admin konfigürasyonu.
    Raporların listelenmesi, düzenlenmesi ve yönetimi.

    Özellikler:
    - Detaylı liste görünümü
    - Gelişmiş arama sistemi
    - Çoklu filtreleme seçenekleri
    - Fieldset ile organize edilmiş form
    - Salt okunur alanlar
    - İlişkili model erişimi

    Liste Görünümü:
    - Rapor adı
    - Rapor türü
    - Departman
    - Oluşturan kullanıcı
    - İlgili şikayet
    - Oluşturma tarihi

    Filtreleme:
    - Rapor türü bazında
    - Departman bazında

    Arama:
    - Rapor adı ve açıklama metinlerinde

    Özel Alanlar:
    - ML analiz sonuçları (salt okunur)
    - Rapor parametreleri
    - Şablon yönetimi
    """

    # Liste görünümünde gösterilecek alanlar
    list_display = (
        "name",  # Rapor adı
        "report_type",  # Rapor türü
        "department",  # Departman
        "created_by",  # Oluşturan kullanıcı
        "complaint",  # İlgili şikayet
        "created_at",  # Oluşturma tarihi
    )

    # Arama yapılabilecek alanlar
    search_fields = (
        "name",  # Rapor adında arama
        "description",  # Açıklama alanında arama
    )

    # Filtreleme seçenekleri (sağ panel)
    list_filter = (
        "report_type",  # Rapor türü filtresi
        "department",  # Departman filtresi
    )

    # Salt okunur alanlar (düzenlenemez)
    readonly_fields = ("ml_analysis",)  # Makine öğrenmesi analiz sonucu

    # Form alanlarının organize edilmesi (fieldset)
    fieldsets = (
        # Ana Bilgiler Bölümü
        (
            None,  # Başlık yok
            {
                "fields": (
                    "name",  # Rapor adı
                    "report_type",  # Rapor türü
                    "department",  # Departman
                    "created_by",  # Oluşturan kullanıcı
                    "complaint",  # İlgili şikayet
                    "format",  # Rapor formatı
                    "is_template",  # Şablon mu?
                    "template",  # Kullanılan şablon
                    "parameters",  # Rapor parametreleri
                    "file",  # Rapor dosyası
                    "ml_analysis",  # ML analizi (salt okunur)
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
            QuerySet: Optimize edilmiş rapor listesi
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "created_by",  # Oluşturan kullanıcı bilgilerini getir
            "department",  # Departman bilgilerini getir
            "complaint",  # İlgili şikayet bilgilerini getir
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
                    "created_by",  # Oluşturan kullanıcıyı değiştiremesin
                    "created_at",  # Oluşturma tarihini değiştiremesin
                ]
            )

        return readonly

    def has_delete_permission(self, request, obj=None):
        """
        Silme yetkisi kontrolü.

        Sadece süper adminler ve rapor sahipleri silebilir.

        Args:
            request: HTTP request nesnesi
            obj: Silinecek nesne

        Returns:
            bool: Silme yetkisi var mı?
        """
        if request.user.is_superuser:
            return True

        # Rapor sahibi kendi raporunu silebilir
        if obj and obj.created_by == request.user:
            return True

        return False

    def has_change_permission(self, request, obj=None):
        """
        Değiştirme yetkisi kontrolü.

        Süper adminler ve rapor sahipleri değiştirebilir.

        Args:
            request: HTTP request nesnesi
            obj: Değiştirilecek nesne

        Returns:
            bool: Değiştirme yetkisi var mı?
        """
        if request.user.is_superuser:
            return True

        # Rapor sahibi kendi raporunu değiştirebilir
        if obj and obj.created_by == request.user:
            return True

        return False

    def save_model(self, request, obj, form, change):
        """
        Model kaydetme işlemi.

        Yeni rapor oluştururken created_by alanını otomatik atar.

        Args:
            request: HTTP request nesnesi
            obj: Kaydedilecek model nesnesi
            form: Admin form nesnesi
            change: Güncelleme mi? (True/False)
        """
        # Yeni rapor oluşturuluyorsa created_by alanını ata
        if not change:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """
        Admin form özelleştirmesi.

        Kullanıcı yetkisine göre form alanlarını düzenler.

        Args:
            request: HTTP request nesnesi
            obj: Düzenlenen nesne
            **kwargs: Ek parametreler

        Returns:
            Form: Özelleştirilmiş admin form
        """
        form = super().get_form(request, obj, **kwargs)

        # Süper admin değilse created_by alanını gizle
        if not request.user.is_superuser and "created_by" in form.base_fields:
            form.base_fields["created_by"].widget.attrs["style"] = "display:none;"

        return form


# Admin site özelleştirmeleri
admin.site.site_header = "Solutio 360 PWA - Raporlama Sistemi"  # Başlık
admin.site.site_title = "Solutio 360 Raporlama"  # Tarayıcı başlığı
admin.site.index_title = "Raporlama Yönetim Paneli"  # Ana sayfa başlığı
