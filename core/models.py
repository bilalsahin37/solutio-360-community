import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import NOTIFICATION_TYPES, WEBHOOK_EVENT_CHOICES


class TimeStampedModel(models.Model):
    """
    Zaman damgalı soyut temel model sınıfı.

    Bu model, oluşturma ve güncelleme zamanlarını otomatik olarak takip eder.
    Diğer modeller bu sınıftan miras alarak zaman damgası özelliği kazanır.

    Attributes:
        created_at: Kaydın oluşturulma zamanı (otomatik)
        updated_at: Kaydın son güncellenme zamanı (otomatik)
        created_by: Kaydı oluşturan kullanıcı
        updated_by: Kaydı son güncelleyen kullanıcı
    """

    # Kayıt oluşturulma zamanı - otomatik olarak şu anki zaman atanır
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)

    # Kayıt güncelleme zamanı - her kaydetmede güncellenir
    updated_at = models.DateTimeField(_("updated at"), auto_now=True, db_index=True)

    # Kaydı oluşturan kullanıcı - foreign key ilişkisi
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
        verbose_name=_("created by"),
    )

    # Kaydı güncelleyen kullanıcı - foreign key ilişkisi
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
        verbose_name=_("updated by"),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(models.Model):
    """
    UUID birincil anahtarlı soyut temel model.

    Bu model, benzersiz UUID'leri birincil anahtar olarak kullanır.
    Bu sayede dış sistemlerle entegrasyon kolaylaşır ve güvenlik artar.

    Attributes:
        id: UUID formatında benzersiz birincil anahtar
    """

    # UUID formatında birincil anahtar - otomatik oluşturulur
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Yumuşak silme özelliği olan soyut temel model.

    Bu model, kayıtları gerçekten silmek yerine "silinmiş" olarak işaretler.
    Bu sayede veri kaybı önlenir ve audit trail korunur.

    Attributes:
        is_active: Kaydın aktif olup olmadığı
        deleted_at: Silinme zamanı
        deleted_by: Silen kullanıcı
    """

    # Kaydın aktif durumu - varsayılan olarak True
    is_active = models.BooleanField(_("is active"), default=True, db_index=True)

    # Silinme zamanı - sadece silindiğinde doldurulur
    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)

    # Silen kullanıcı bilgisi
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_deleted",
        verbose_name=_("deleted by"),
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, user=None):
        """
        Yumuşak silme işlemi.

        Kaydı veritabanından silmek yerine is_active=False yapar
        ve silme zamanını kaydeder.

        Args:
            using: Veritabanı bağlantısı
            keep_parents: Parent kayıtları koruma
            user: Silme işlemini yapan kullanıcı
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """
        Gerçek silme işlemi.

        Kaydı veritabanından tamamen siler.
        Dikkatli kullanılmalı!

        Args:
            using: Veritabanı bağlantısı
            keep_parents: Parent kayıtları koruma
        """
        return super().delete(using=using, keep_parents=keep_parents)


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Temel model sınıfı.

    UUID, zaman damgası ve yumuşak silme özelliklerini birleştirir.
    Çoğu model bu sınıftan miras alarak tüm temel özellikleri kazanır.
    """

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """
    Denetim günlüğü modeli.

    Sistemdeki tüm değişiklikleri takip eder.
    Kim, ne zaman, neyi, nasıl değiştirdi bilgilerini saklar.

    Bu model güvenlik ve uyumluluk açısından kritiktir.
    """

    # Yapılabilecek işlem türleri
    ACTION_CHOICES = (
        ("CREATE", _("Create")),
        ("UPDATE", _("Update")),
        ("DELETE", _("Delete")),
        ("RESTORE", _("Restore")),
    )

    # Benzersiz kayıt kimliği
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # İşlem zamanı - otomatik olarak şu anki zaman
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # İşlemi yapan kullanıcı
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Yapılan işlem türü
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)

    # Değişiklik yapılan model adı
    model_name = models.CharField(max_length=255)

    # Değişiklik yapılan objenin ID'si
    object_id = models.UUIDField()

    # Yapılan değişiklikler (JSON formatında)
    changes = models.JSONField()

    # İşlemi yapan IP adresi
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Browser/client bilgisi
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _("audit log")
        verbose_name_plural = _("audit logs")
        ordering = ["-timestamp"]
        indexes = [
            # Performans için indexler
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["user", "action"]),
        ]

    def __str__(self):
        """
        Denetim kaydının string temsili.

        Returns:
            str: İşlem özeti
        """
        return f"{self.action} on {self.model_name} by {self.user} at {self.timestamp}"


class SystemSettings(models.Model):
    """
    Sistem ayarları modeli.

    Uygulama genelinde kullanılan ayarları saklar.
    Bu sayede ayarlar veritabanından dinamik olarak okunabilir.

    Attributes:
        key: Ayar anahtarı (benzersiz)
        value: Ayar değeri (JSON formatında)
        description: Ayar açıklaması
        is_public: Herkese açık mı?
    """

    # Ayar anahtarı - benzersiz olmalı
    key = models.CharField(max_length=255, unique=True, db_index=True)

    # Ayar değeri - JSON formatında saklanır
    value = models.JSONField()

    # Ayar açıklaması
    description = models.TextField(blank=True)

    # Bu ayar herkese açık mı? (API'de döndürülür mü?)
    is_public = models.BooleanField(default=False)

    # Kayıt zamanları
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("system setting")
        verbose_name_plural = _("system settings")
        ordering = ["key"]

    def __str__(self):
        """
        Sistem ayarının string temsili.

        Returns:
            str: Ayar anahtarı
        """
        return self.key

    @classmethod
    def get_setting(cls, key, default=None):
        """
        Sistem ayarı değerini getir.

        Args:
            key (str): Ayar anahtarı
            default: Varsayılan değer (ayar bulunamazsa)

        Returns:
            Ayar değeri veya varsayılan değer
        """
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, description="", is_public=False):
        """
        Sistem ayarı değerini ayarla.

        Args:
            key (str): Ayar anahtarı
            value: Ayar değeri
            description (str): Ayar açıklaması
            is_public (bool): Herkese açık mı?

        Returns:
            SystemSettings: Oluşturulan veya güncellenen ayar
        """
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                "value": value,
                "description": description,
                "is_public": is_public,
            },
        )

        # Eğer ayar zaten varsa güncelle
        if not created:
            setting.value = value
            setting.description = description
            setting.is_public = is_public
            setting.save()

        return setting


# Create your models here.


class WebhookEventType(models.Model):
    """
    Webhook olay türleri modeli.

    Dış sistemlere gönderilecek webhook olaylarının türlerini tanımlar.
    Örnek: complaint_created, complaint_updated, vb.
    """

    # Olay kodu - benzersiz tanımlayıcı
    code = models.CharField(max_length=32, unique=True)

    # Olay adı - kullanıcı dostu isim
    name = models.CharField(max_length=64)

    def __str__(self):
        """
        Webhook olay türünün string temsili.

        Returns:
            str: Olay adı
        """
        return self.name


class NotificationType(models.Model):
    """
    Bildirim türleri modeli.

    Sistemdeki farklı bildirim türlerini tanımlar.
    Örnek: email, sms, push_notification, vb.
    """

    # Bildirim kodu - benzersiz tanımlayıcı
    code = models.CharField(max_length=32, unique=True)

    # Bildirim adı - kullanıcı dostu isim
    name = models.CharField(max_length=64)

    def __str__(self):
        """
        Bildirim türünün string temsili.

        Returns:
            str: Bildirim adı
        """
        return self.name


class Notification(models.Model):
    """
    Kullanıcı bildirimleri modeli.

    Kullanıcılara gönderilen bildirimleri saklar.
    Dashboard'da ve bildirim panelinde görüntülenir.
    """

    # Bildirim gönderilecek kullanıcı
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_notifications",
    )

    # Bildirim mesajı
    message = models.CharField(max_length=255)

    # Bildirime tıklandığında gidilecek URL
    url = models.CharField(max_length=255, blank=True)

    # Bildirim okundu mu?
    is_read = models.BooleanField(default=False)

    # Bildirim oluşturulma zamanı
    created_at = models.DateTimeField(auto_now_add=True)

    # Bildirim türü
    type = models.ForeignKey(NotificationType, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        """
        Bildirimin string temsili.

        Returns:
            str: Bildirim özeti
        """
        return f"{self.user.username} - {self.message[:50]}"


class Webhook(models.Model):
    """
    Webhook konfigürasyon modeli.

    Dış sistemlere HTTP POST istekleri gönderir.
    Belirli olaylar gerçekleştiğinde otomatik tetiklenir.
    """

    # Webhook gönderilecek URL
    url = models.URLField()

    # Hangi olayda tetiklenecek
    event = models.ForeignKey(WebhookEventType, on_delete=models.CASCADE)

    # Webhook aktif mi?
    is_active = models.BooleanField(default=True)

    # Webhook oluşturulma zamanı
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Webhook'un string temsili.

        Returns:
            str: Webhook özeti
        """
        return f"{self.event.name} -> {self.url}"
