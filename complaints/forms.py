"""
Şikayet Yönetimi Form Sınıfları - Solutio 360 PWA
=================================================

Bu modül şikayet sistemi için Django form sınıflarını içerir.
Modern, responsive ve kullanıcı dostu form arayüzleri sunar.

Ana Özellikler:
- Şikayet oluşturma ve düzenleme formları
- Yorum ekleme formları
- Tailwind CSS ile modern tasarım
- Dosya yükleme desteği
- Form validasyonu ve güvenlik
- Responsive tasarım
- Accessibility (erişilebilirlik) desteği

Form Türleri:
- ComplaintForm: Şikayet oluşturma/düzenleme
- CommentForm: Yorum ekleme

Tasarım Özellikleri:
- Modern input stilleri
- Focus durumları
- Placeholder metinleri
- Responsive boyutlandırma
- Görsel geri bildirim
"""

from django import forms
from django.contrib.auth import get_user_model

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

# Django'nun kullanıcı modelini al
User = get_user_model()


class ComplaintForm(forms.ModelForm):
    """
    Şikayet Oluşturma/Düzenleme Formu
    =================================

    Modern ve kullanıcı dostu şikayet başvuru formu.
    Responsive tasarım ve Tailwind CSS stilleri ile.

    Ana Alanlar:
    - title: Şikayet başlığı/konusu
    - description: Detaylı şikayet metni

    Özellikler:
    - Otomatik stil uygulaması
    - Placeholder metinleri
    - Responsive tasarım
    - Focus durumları
    - Dosya yükleme desteği
    - Form validasyonu

    Kullanım:
    - Yeni şikayet oluşturma
    - Mevcut şikayet düzenleme
    - Çoklu dosya yükleme
    - Etiket atama (view'da yapılır)
    """

    class Meta:
        model = Complaint  # Şikayet modeli ile bağlantı
        fields = ["title", "description"]  # Formda gösterilecek alanlar

        # Widget'lar - HTML form elemanları ve özellikleri
        widgets = {
            # Açıklama alanı - çok satırlı metin kutusu
            "description": forms.Textarea(
                attrs={
                    "rows": 5,  # Başlangıç yüksekliği
                    "placeholder": "Şikayet metninizi yazınız...",  # Yardımcı metin
                }
            ),
            # Başlık alanı - tek satır metin kutusu
            "title": forms.TextInput(attrs={"placeholder": "Konu/Başlık"}),  # Yardımcı metin
        }

    def __init__(self, *args, **kwargs):
        """
        Form başlatma işlemi.

        Formun başlatılması sırasında çalışır.
        Stil uygulaması ve alan düzenlemeleri yapar.

        Args:
            *args: Pozisyonel argümanlar
            **kwargs: Anahtar kelime argümanları
                show_reviewers: Değerlendirici alanlarını göster mi?
        """
        # Değerlendirici alanlarını gösterme seçeneği
        show_reviewers = kwargs.pop("show_reviewers", False)

        # Üst sınıfın __init__ metodunu çağır
        super().__init__(*args, **kwargs)

        # Eğer değerlendiriciler gösterilmeyecekse bu alanları kaldır
        if not show_reviewers:
            self.fields.pop("reviewers", None)  # Değerlendiriciler alanını kaldır
            self.fields.pop("inspectors", None)  # Denetçiler alanını kaldır

        # Modern ve responsive input stilleri - Tailwind CSS sınıfları
        # Temel stil sınıfları tüm input'lar için ortak
        base_class = (
            "w-full "  # Tam genişlik
            "px-4 py-2 "  # İç boşluklar
            "rounded-lg "  # Yuvarlatılmış köşeler
            "border border-gray-300 "  # Kenarlık
            "focus:border-blue-500 "  # Focus durumunda mavi kenarlık
            "focus:ring-2 focus:ring-blue-100 "  # Focus durumunda mavi halka
            "transition-all duration-200 "  # Yumuşak geçişler
            "bg-gray-50 "  # Açık gri arka plan
            "placeholder-gray-400 "  # Placeholder rengi
            "text-base "  # Metin boyutu
            "shadow-sm"  # Hafif gölge
        )

        # Her form alanı için uygun stil uygula
        for name, field in self.fields.items():
            # Çoklu seçim kutuları (SelectMultiple)
            if isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs["class"] = base_class + " min-h-[60px] min-w-[180px]"

            # Tekli seçim kutuları (Select)
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = base_class

            # Çok satırlı metin kutuları (Textarea)
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = base_class + " resize-vertical min-h-[100px]"

            # Dosya yükleme alanları (FileInput)
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = (
                    "block w-full text-sm text-gray-700 "
                    "border border-gray-300 rounded-lg "
                    "cursor-pointer bg-gray-50 "
                    "focus:outline-none focus:border-blue-500 "
                    "focus:ring-2 focus:ring-blue-100"
                )

            # Diğer tüm input türleri (TextInput, EmailInput, vs.)
            else:
                field.widget.attrs["class"] = base_class

    def save(self, commit=True, user=None):
        """
        Form kaydetme işlemi.

        Formu veritabanına kaydeder ve ilgili işlemleri yapar.
        Dosya ekleri ve kullanıcı ataması dahil.

        Args:
            commit (bool): Hemen veritabanına kaydet mi?
            user: Şikayeti oluşturan kullanıcı

        Returns:
            Complaint: Kaydedilen şikayet nesnesi
        """
        # Form verilerinden model nesnesi oluştur (henüz kaydetme)
        instance = super().save(commit=False)

        # Kullanıcı bilgisi varsa ata
        if user is not None:
            instance.user = user

        # Eğer commit=True ise veritabanına kaydet
        if commit:
            instance.save()  # Ana nesneyi kaydet
            self.save_m2m()  # Many-to-many ilişkileri kaydet

            # Dosya eklerini kaydet
            files = self.files.getlist("attachments")
            for f in files:
                # Her dosya için ComplaintAttachment nesnesi oluştur
                ComplaintAttachment.objects.create(
                    complaint=instance,  # Şikayet ilişkisi
                    file=f,  # Dosya
                    filename=f.name,  # Dosya adı
                    file_type=f.content_type,  # MIME tipi (image/jpeg, text/pdf vs.)
                    file_size=f.size,  # Dosya boyutu (byte)
                )

        return instance

    def clean_is_public(self):
        """
        is_public alanı validasyonu.

        String değerini boolean'a çevirir.

        Returns:
            bool: Herkese açık mı?
        """
        value = self.cleaned_data.get("is_public")
        return value == "True"

    def clean_is_anonymous(self):
        """
        is_anonymous alanı validasyonu.

        String değerini boolean'a çevirir.

        Returns:
            bool: Anonim mi?
        """
        value = self.cleaned_data.get("is_anonymous")
        return value == "True"

    def clean_is_urgent(self):
        """
        is_urgent alanı validasyonu.

        String değerini boolean'a çevirir.

        Returns:
            bool: Acil mi?
        """
        value = self.cleaned_data.get("is_urgent")
        return value == "True"


class CommentForm(forms.ModelForm):
    """
    Yorum Ekleme Formu
    ==================

    Şikayetlere yorum ekleme için kullanılan form.
    Basit ve kullanıcı dostu tasarım.

    Ana Alanlar:
    - content: Yorum içeriği
    - is_internal: Dahili yorum mu? (sadece personel görebilir)

    Özellikler:
    - Çok satırlı metin alanı
    - İç/dış yorum seçimi
    - Dosya eki desteği
    - Otomatik kullanıcı ataması

    Kullanım:
    - Şikayet detay sayfasında
    - AJAX ile dinamik ekleme
    - Bildirim sistemi entegrasyonu
    """

    class Meta:
        model = ComplaintComment  # Yorum modeli ile bağlantı
        fields = ["content", "is_internal"]  # Formda gösterilecek alanlar

        # Widget'lar - HTML form elemanları
        widgets = {
            # Yorum içeriği - çok satırlı metin kutusu
            "content": forms.Textarea(
                attrs={
                    "rows": 3,  # Başlangıç yüksekliği
                    "placeholder": "Yorumunuzu yazın...",  # Yardımcı metin
                    "class": (
                        "w-full px-3 py-2 border border-gray-300 "
                        "rounded-lg focus:ring-2 focus:ring-blue-500 "
                        "focus:border-blue-500 resize-vertical"
                    ),
                }
            ),
            # Dahili yorum checkbox'ı
            "is_internal": forms.CheckboxInput(
                attrs={
                    "class": "rounded border-gray-300 text-blue-600 "
                    "focus:ring-blue-500 focus:ring-2"
                }
            ),
        }

        # Alan etiketleri
        labels = {
            "content": "Yorum",
            "is_internal": "Dahili yorum (sadece personel görebilir)",
        }

        # Yardım metinleri
        help_texts = {
            "content": "Yorumunuzu buraya yazın. Maksimum 1000 karakter.",
            "is_internal": "İşaretlerseniz bu yorum sadece yetkili personel tarafından görülebilir.",
        }

    def __init__(self, *args, **kwargs):
        """
        Form başlatma işlemi.

        Formun başlatılması sırasında çalışır.
        Ek stil ve davranış düzenlemeleri yapar.

        Args:
            *args: Pozisyonel argümanlar
            **kwargs: Anahtar kelime argümanları
        """
        super().__init__(*args, **kwargs)

        # Alan özelliklerini düzenle
        self.fields["content"].required = True  # Zorunlu alan
        self.fields["is_internal"].required = False  # İsteğe bağlı alan

        # Placeholder metinlerini güncelle
        self.fields["content"].widget.attrs.update({"placeholder": "Yorumunuzu buraya yazın..."})

    def clean_content(self):
        """
        Yorum içeriği validasyonu.

        Yorum içeriğinin uygunluğunu kontrol eder.

        Returns:
            str: Temizlenmiş yorum içeriği

        Raises:
            ValidationError: İçerik uygun değilse
        """
        content = self.cleaned_data.get("content")

        # Boş içerik kontrolü
        if not content or not content.strip():
            raise forms.ValidationError("Yorum içeriği boş olamaz.")

        # Minimum uzunluk kontrolü
        if len(content.strip()) < 5:
            raise forms.ValidationError("Yorum en az 5 karakter olmalıdır.")

        # Maksimum uzunluk kontrolü
        if len(content) > 1000:
            raise forms.ValidationError("Yorum maksimum 1000 karakter olabilir.")

        # Spam/kötü içerik kontrolü (basit)
        spam_words = ["spam", "reklam", "satış"]
        content_lower = content.lower()
        for word in spam_words:
            if word in content_lower:
                raise forms.ValidationError("Uygunsuz içerik tespit edildi.")

        return content.strip()

    def save(self, commit=True):
        """
        Yorum kaydetme işlemi.

        Yorumu veritabanına kaydeder.

        Args:
            commit (bool): Hemen veritabanına kaydet mi?

        Returns:
            ComplaintComment: Kaydedilen yorum nesnesi
        """
        # Form verilerinden model nesnesi oluştur
        instance = super().save(commit=False)

        # Oluşturma zamanını ayarla
        if not instance.created_at:
            from django.utils import timezone

            instance.created_at = timezone.now()

        # Veritabanına kaydet
        if commit:
            instance.save()

        return instance
