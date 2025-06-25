from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from users.models import Department, User


class ComplaintCategory(BaseModel):
    """
    Şikayet kategorileri modeli.

    Şikayetlerin sınıflandırılması için kullanılır.
    Hiyerarşik yapı destekler (ana kategori - alt kategori).
    SLA süreleri ve sorumlu departmanlar atanabilir.
    """

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True)

    # Hiyerarşik yapı için parent kategori
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent category"),
    )

    icon = models.CharField(_("icon"), max_length=50, blank=True)
    color = models.CharField(_("color"), max_length=7, default="#000000")
    order = models.PositiveIntegerField(_("order"), default=0)

    # SLA - Service Level Agreement (hizmet seviyesi anlaşması)
    sla_hours = models.PositiveIntegerField(_("SLA hours"), default=24)

    # Bu kategori için sorumlu departman
    responsible_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name="responsible_categories",
        verbose_name=_("responsible department"),
    )

    class Meta:
        verbose_name = _("complaint category")
        verbose_name_plural = _("complaint categories")
        ordering = ["order", "name"]
        unique_together = ["name", "parent"]

    def __str__(self):
        """Kategori adını döndürür. Parent varsa "Ana > Alt" formatında."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        """Kategori detay sayfası URL'si."""
        from django.urls import reverse

        return reverse("complaints:category-detail", args=[str(self.id)])


class Priority(models.Model):
    """
    Şikayet öncelik seviyeleri modeli.

    Şikayetlerin önem derecesini belirler.
    1-5 arası seviye (1: En düşük, 5: En yüksek/Acil)
    Her öncelik seviyesi için yanıt süresi belirlenebilir.
    """

    name = models.CharField(_("Öncelik Adı"), max_length=50)

    # Öncelik seviyesi (1-5 arası)
    level = models.IntegerField(
        _("Öncelik Seviyesi"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        unique=True,
    )

    color = models.CharField(_("Renk Kodu"), max_length=7, default="#000000")
    description = models.TextField(_("Açıklama"), blank=True)

    # Bu öncelik için beklenen yanıt süresi
    response_time = models.DurationField(_("Yanıt Süresi"))

    is_active = models.BooleanField(_("Aktif"), default=True)

    class Meta:
        verbose_name = _("Öncelik")
        verbose_name_plural = _("Öncelikler")
        ordering = ["level"]

    def __str__(self):
        """Öncelik adı ve seviyesi."""
        return f"{self.name} (Seviye: {self.level})"


class Status(models.Model):
    """
    Şikayet durumları modeli.

    Şikayetin hangi aşamada olduğunu belirler.
    Workflow yönetimi için kullanılır.
    """

    name = models.CharField(_("Durum Adı"), max_length=50)
    code = models.SlugField(_("Durum Kodu"), max_length=50, unique=True)
    color = models.CharField(_("Renk Kodu"), max_length=7, default="#000000")
    description = models.TextField(_("Açıklama"), blank=True)

    # Son durum mu? (çözüldü, reddedildi vb.)
    is_final = models.BooleanField(_("Son Durum"), default=False)

    is_active = models.BooleanField(_("Aktif"), default=True)
    order = models.IntegerField(_("Sıralama"), default=0)

    class Meta:
        verbose_name = _("Durum")
        verbose_name_plural = _("Durumlar")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Institution(models.Model):
    """Şikayet edilen kurum modeli."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    """Kurum altındaki birim modeli."""

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="units"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.institution} / {self.name}"


class Subunit(models.Model):
    """Birim altındaki alt birim modeli."""

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="subunits")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.unit} / {self.name}"


class Person(models.Model):
    """Şikayet edilen kişi modeli."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="people",
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="people"
    )
    subunit = models.ForeignKey(
        Subunit, on_delete=models.SET_NULL, null=True, blank=True, related_name="people"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Complaint(BaseModel):
    """
    Ana şikayet modeli.

    Sistemin kalbi olan model. Tüm şikayet bilgilerini saklar:
    - Temel bilgiler (başlık, açıklama, kategori)
    - Durum ve öncelik bilgileri
    - Atama bilgileri (kim oluşturdu, kime atandı)
    - Tarih bilgileri (oluşturma, son tarih, çözüm tarihi)
    - Memnuniyet değerlendirmesi
    - Geri çekme/iptal durumu
    """

    # Şikayet durumu seçenekleri
    STATUS_CHOICES = (
        ("DRAFT", _("Draft")),  # Taslak
        ("SUBMITTED", _("Submitted")),  # Gönderildi
        ("IN_REVIEW", _("In Review")),  # İnceleniyor
        ("IN_PROGRESS", _("In Progress")),  # İşlemde
        ("RESOLVED", _("Resolved")),  # Çözüldü
        ("CLOSED", _("Closed")),  # Kapatıldı
        ("REOPENED", _("Reopened")),  # Yeniden açıldı
        ("CANCELLED", _("Cancelled")),  # İptal edildi
        ("WITHDRAWN", _("Withdrawn")),  # Geri çekildi
    )

    # Öncelik seçenekleri
    PRIORITY_CHOICES = (
        ("LOW", _("Low")),  # Düşük
        ("MEDIUM", _("Medium")),  # Orta
        ("HIGH", _("High")),  # Yüksek
        ("CRITICAL", _("Critical")),  # Kritik
    )

    # Temel bilgiler
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"))

    # Kategori ilişkisi
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.PROTECT,
        related_name="complaints",
        verbose_name=_("category"),
        null=True,
        blank=True,
    )

    # Durum ve öncelik
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="DRAFT"
    )
    priority = models.CharField(
        _("priority"), max_length=20, choices=PRIORITY_CHOICES, default="MEDIUM"
    )

    # Kullanıcı ilişkileri
    submitter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="submitted_complaints",
        verbose_name=_("submitter"),
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_complaints",
        verbose_name=_("assigned to"),
    )

    # Departman ilişkisi
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="complaints",
        verbose_name=_("department"),
    )

    # Tarih bilgileri
    due_date = models.DateTimeField(_("due date"), null=True, blank=True)
    resolution_date = models.DateTimeField(_("resolution date"), null=True, blank=True)

    # Çözüm bilgileri
    resolution = models.TextField(_("resolution"), blank=True)

    # Memnuniyet değerlendirmesi (1-5 yıldız)
    satisfaction_rating = models.PositiveSmallIntegerField(
        _("satisfaction rating"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    satisfaction_comment = models.TextField(_("satisfaction comment"), blank=True)

    # Gizlilik ayarları
    is_anonymous = models.BooleanField(_("is anonymous"), default=False)
    is_confidential = models.BooleanField(_("is confidential"), default=False)

    # Geri çekme/iptal bilgileri
    is_withdrawn = models.BooleanField(_("is withdrawn"), default=False)
    withdrawal_date = models.DateTimeField(_("withdrawal date"), null=True, blank=True)
    withdrawal_reason = models.TextField(_("withdrawal reason"), blank=True)
    can_be_withdrawn = models.BooleanField(_("can be withdrawn"), default=True)

    # İlişkili veriler
    tags = models.ManyToManyField(
        "ComplaintTag", blank=True, related_name="complaints", verbose_name=_("tags")
    )

    # Enhanced AI Analysis Results - LeewayHertz Style
    ai_analysis = models.JSONField(_("AI analysis"), default=dict, blank=True)
    sentiment_score = models.FloatField(_("sentiment score"), null=True, blank=True)
    urgency_level = models.CharField(
        _("urgency level"), max_length=20, default="medium"
    )
    emotional_intensity = models.CharField(
        _("emotional intensity"), max_length=20, default="medium"
    )
    formality_level = models.CharField(
        _("formality level"), max_length=20, default="neutral"
    )
    auto_response = models.TextField(_("auto response"), blank=True)

    # Department Routing - Enhanced
    assigned_department = models.CharField(
        _("assigned department"), max_length=50, blank=True
    )
    routing_confidence = models.FloatField(
        _("routing confidence"), null=True, blank=True
    )
    escalation_path = models.JSONField(_("escalation path"), default=list, blank=True)

    # Processing Timestamps
    ai_processed_at = models.DateTimeField(_("AI processed at"), null=True, blank=True)
    auto_response_sent_at = models.DateTimeField(
        _("auto response sent at"), null=True, blank=True
    )

    # Multi-language Support
    detected_language = models.CharField(
        _("detected language"), max_length=10, default="tr"
    )
    cultural_context = models.JSONField(_("cultural context"), default=dict, blank=True)

    class Meta:
        verbose_name = _("complaint")
        verbose_name_plural = _("complaints")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["submitter", "assigned_to"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        """Şikayet başlığı."""
        return self.title

    def get_absolute_url(self):
        """Şikayet detay sayfası URL'si."""
        return reverse("complaints:complaint-detail", args=[str(self.id)])

    def save(self, *args, **kwargs):
        """Kaydetme işlemi sırasında otomatik işlemler."""
        # İlk kez kaydediliyorsa due_date ayarla
        if not self.pk and self.category and self.category.sla_hours:
            self.due_date = timezone.now() + timezone.timedelta(
                hours=self.category.sla_hours
            )
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Şikayet süresi geçmiş mi?"""
        if self.due_date and self.status not in ["RESOLVED", "CLOSED", "CANCELLED"]:
            return timezone.now() > self.due_date
        return False

    @property
    def sla_status(self):
        """SLA durumu (yeşil/sarı/kırmızı)."""
        if not self.due_date or self.status in ["RESOLVED", "CLOSED"]:
            return "completed"

        time_left = self.due_date - timezone.now()
        if time_left.total_seconds() < 0:
            return "overdue"  # Süresi geçmiş
        elif time_left.total_seconds() < 3600:  # 1 saat kala
            return "warning"  # Uyarı
        else:
            return "ok"  # Normal

    @property
    def can_withdraw(self):
        """Şikayet geri çekilebilir mi?"""
        if not self.can_be_withdrawn:
            return False
        if self.is_withdrawn:
            return False
        if self.status in ["RESOLVED", "CLOSED", "CANCELLED", "WITHDRAWN"]:
            return False
        return True

    def withdraw(self, reason="", user=None):
        """
        Şikayeti geri çek.

        Args:
            reason: Geri çekme sebebi
            user: İşlemi yapan kullanıcı
        """
        if not self.can_withdraw:
            raise ValueError("Bu şikayet geri çekilemez")

        self.is_withdrawn = True
        self.withdrawal_date = timezone.now()
        self.withdrawal_reason = reason
        self.status = "WITHDRAWN"
        self.save(
            update_fields=[
                "is_withdrawn",
                "withdrawal_date",
                "withdrawal_reason",
                "status",
            ]
        )

    def cancel(self, reason="", user=None):
        """
        Şikayeti iptal et.

        Args:
            reason: İptal sebebi
            user: İşlemi yapan kullanıcı
        """
        self.status = "CANCELLED"
        self.save(update_fields=["status"])


class ComplaintAttachment(BaseModel):
    """
    Şikayete eklenen dosyalar modeli.

    Şikayetlere ek olarak dosya, resim vb. eklenebilir.
    Dosya türü ve boyutu kontrol edilir.
    """

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("complaint"),
    )
    file = models.FileField(_("file"), upload_to="complaints/attachments/%Y/%m/")
    filename = models.CharField(_("filename"), max_length=255)
    file_type = models.CharField(_("file type"), max_length=100)
    file_size = models.PositiveIntegerField(_("file size"))
    description = models.CharField(_("description"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("complaint attachment")
        verbose_name_plural = _("complaint attachments")
        ordering = ["-created_at"]

    def __str__(self):
        """Dosya adı."""
        return self.filename


class ComplaintComment(BaseModel):
    """
    Şikayet yorumları ve mesajlaşma modeli.

    Şikayet üzerinde yorum yapılabilir ve mesajlaşma sağlanır.
    İç yorumlar (personel arası) ve dış yorumlar (kullanıcı ile) ayrılır.
    """

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("complaint"),
    )
    content = models.TextField(_("content"))

    # İç yorum mu? (sadece personel görebilir)
    is_internal = models.BooleanField(_("is internal"), default=False)

    # Üst yorum (yanıt zinciri için)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("parent comment"),
    )

    # Gönderen ve alıcı
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_comments",
        verbose_name=_("Gönderen"),
        null=True,
        blank=True,
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_comments",
        verbose_name=_("Alıcı"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("complaint comment")
        verbose_name_plural = _("complaint comments")
        ordering = ["created_at"]

    def __str__(self):
        """Yorum içeriğinin ilk 50 karakteri."""
        return f"{self.content[:50]}..."


class ComplaintTag(BaseModel):
    """
    Şikayet etiketleri modeli.

    Şikayetlerin etiketlenmesi ve kategorize edilmesi için kullanılır.
    """

    name = models.CharField(_("name"), max_length=50, unique=True)
    color = models.CharField(_("color"), max_length=7, default="#000000")
    description = models.CharField(_("description"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("complaint tag")
        verbose_name_plural = _("complaint tags")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ComplaintWorkflow(BaseModel):
    """
    Şikayet iş akışı geçiş modeli.

    Şikayetin durum değişikliklerini takip eder.
    Audit trail için kullanılır.
    """

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="workflow_transitions",
        verbose_name=_("complaint"),
    )
    from_status = models.CharField(
        _("from status"), max_length=20, choices=Complaint.STATUS_CHOICES
    )
    to_status = models.CharField(
        _("to status"), max_length=20, choices=Complaint.STATUS_CHOICES
    )
    comment = models.TextField(_("comment"), blank=True)
    transition_time = models.DateTimeField(_("transition time"), auto_now_add=True)

    class Meta:
        verbose_name = _("complaint workflow")
        verbose_name_plural = _("complaint workflows")
        ordering = ["-transition_time"]

    def __str__(self):
        """Durum geçişi açıklaması."""
        return f"{self.from_status} -> {self.to_status}"


class ComplaintNotification(BaseModel):
    """
    Şikayet bildirimleri modeli.

    Şikayet ile ilgili bildirimler kullanıcılara gönderilir.
    """

    NOTIFICATION_TYPES = (
        ("STATUS_CHANGE", _("Status Change")),  # Durum değişikliği
        ("ASSIGNMENT", _("Assignment")),  # Atama
        ("COMMENT", _("Comment")),  # Yorum
        ("DUE_DATE", _("Due Date")),  # Son tarih uyarısı
        ("RESOLUTION", _("Resolution")),  # Çözüm
    )

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("complaint"),
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="complaint_notifications",
        verbose_name=_("recipient"),
    )
    notification_type = models.CharField(
        _("notification type"), max_length=20, choices=NOTIFICATION_TYPES
    )
    message = models.TextField(_("message"))
    is_read = models.BooleanField(_("is read"), default=False)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)

    class Meta:
        verbose_name = _("complaint notification")
        verbose_name_plural = _("complaint notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["complaint", "notification_type"]),
        ]

    def __str__(self):
        """Bildirim açıklaması."""
        return f"{self.recipient.username} - {self.get_notification_type_display()}"

    def mark_as_read(self):
        """Bildirimi okundu olarak işaretle."""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])


def analyze_complaint_text(text):
    """
    Şikayet metnini makine öğrenmesi ile analiz et.

    Bu fonksiyon şikayet metnini analiz ederek:
    - Duygu analizi (pozitif/negatif/nötr)
    - Anahtar kelime çıkarımı
    - Kategori önerisi
    - Öncelik tahmini
    yapabilir.

    Args:
        text (str): Analiz edilecek metin

    Returns:
        dict: Analiz sonuçları
    """
    # TODO: Gerçek ML analizi implementasyonu
    # Şimdilik basit bir mock döndürüyoruz
    return {
        "sentiment": "neutral",
        "keywords": [],
        "suggested_category": None,
        "suggested_priority": "MEDIUM",
        "confidence": 0.5,
    }
