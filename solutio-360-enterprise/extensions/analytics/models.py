"""
Analytics Models - ML sistemi için veritabanı modelleri
Makine öğrenmesi metrikleri, öngörüler ve performans takibi
"""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class MLInsight(models.Model):
    """
    Makine öğrenmesi tarafından üretilen akıllı öneriler
    """

    PRIORITY_CHOICES = [
        ("low", "Düşük"),
        ("medium", "Orta"),
        ("high", "Yüksek"),
        ("critical", "Kritik"),
    ]

    INSIGHT_TYPES = [
        ("prediction", "Tahmin"),
        ("anomaly", "Anomali"),
        ("trend", "Trend"),
        ("optimization", "Optimizasyon"),
        ("alert", "Uyarı"),
    ]

    title = models.CharField(max_length=200, verbose_name="Başlık")

    description = models.TextField(verbose_name="Açıklama")

    insight_type = models.CharField(
        max_length=20,
        choices=INSIGHT_TYPES,
        default="prediction",
        verbose_name="Öngörü Türü",
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
        verbose_name="Öncelik",
    )

    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Güven Skoru (%)",
        help_text="0-100 arası güven skoru",
    )

    # JSON formatında ek veriler
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Ek Veriler")

    # İkon ve stil bilgileri
    icon = models.CharField(
        max_length=50, default="fas fa-lightbulb", verbose_name="İkon CSS Sınıfı"
    )

    # Durum bilgileri
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    is_applied = models.BooleanField(default=False, verbose_name="Uygulandı mı?")

    # Tarih bilgileri
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="Oluşturulma Tarihi"
    )

    applied_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Uygulanma Tarihi"
    )

    dismissed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Reddedilme Tarihi"
    )

    # Kullanıcı ilişkileri
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applied_insights",
        verbose_name="Uygulayan Kullanıcı",
    )

    dismissed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dismissed_insights",
        verbose_name="Reddeden Kullanıcı",
    )

    class Meta:
        verbose_name = "ML Öngörüsü"
        verbose_name_plural = "ML Öngörüleri"
        ordering = ["-created_at", "-confidence"]
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
            models.Index(fields=["priority", "confidence"]),
            models.Index(fields=["insight_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.confidence:.1f}%)"

    @property
    def age_in_hours(self):
        """Öngörünün yaşı (saat cinsinden)"""
        return (timezone.now() - self.created_at).total_seconds() / 3600

    @property
    def is_recent(self):
        """Son 24 saat içinde oluşturuldu mu?"""
        return self.age_in_hours <= 24


class AnomalyDetection(models.Model):
    """
    Anomali tespiti kayıtları
    """

    SEVERITY_CHOICES = [
        ("low", "Düşük"),
        ("medium", "Orta"),
        ("high", "Yüksek"),
        ("critical", "Kritik"),
    ]

    title = models.CharField(max_length=200, verbose_name="Anomali Başlığı")

    description = models.TextField(verbose_name="Açıklama")

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default="medium",
        verbose_name="Önem Derecesi",
    )

    anomaly_score = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        verbose_name="Anomali Skoru",
        help_text="-1 ile 1 arasında anomali skoru",
    )

    # Tespit edilen veri noktası
    data_point = models.JSONField(default=dict, verbose_name="Veri Noktası")

    # İlgili şikayet (varsa)
    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="anomalies",
        verbose_name="İlgili Şikayet",
    )

    # Tespit tarihi
    detected_at = models.DateTimeField(
        default=timezone.now, verbose_name="Tespit Tarihi"
    )

    # Çözüm durumu
    is_resolved = models.BooleanField(default=False, verbose_name="Çözüldü mü?")

    resolved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Çözülme Tarihi"
    )

    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_anomalies",
        verbose_name="Çözen Kullanıcı",
    )

    class Meta:
        verbose_name = "Anomali Tespiti"
        verbose_name_plural = "Anomali Tespitleri"
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["detected_at", "severity"]),
            models.Index(fields=["is_resolved"]),
            models.Index(fields=["anomaly_score"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"

    @property
    def age_in_hours(self):
        """Anomalinin yaşı (saat cinsinden)"""
        return (timezone.now() - self.detected_at).total_seconds() / 3600


class ModelPerformance(models.Model):
    """
    ML model performans metrikleri
    """

    MODEL_TYPES = [
        ("anomaly_detection", "Anomali Tespiti"),
        ("sentiment_analysis", "Duygu Analizi"),
        ("category_prediction", "Kategori Tahmini"),
        ("resolution_prediction", "Çözüm Tahmini"),
        ("incremental_classifier", "Artımlı Sınıflandırıcı"),
        ("reinforcement_learning", "Pekiştirmeli Öğrenme"),
    ]

    model_name = models.CharField(
        max_length=50, choices=MODEL_TYPES, verbose_name="Model Adı"
    )

    model_version = models.CharField(
        max_length=20, default="1.0.0", verbose_name="Model Versiyonu"
    )

    # Performans metrikleri
    accuracy = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Doğruluk (Accuracy)",
    )

    precision = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Hassasiyet (Precision)",
    )

    recall = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Geri Çağırma (Recall)",
    )

    f1_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="F1 Skoru",
    )

    # Ek metrikler
    training_samples = models.PositiveIntegerField(
        default=0, verbose_name="Eğitim Örnek Sayısı"
    )

    test_samples = models.PositiveIntegerField(
        default=0, verbose_name="Test Örnek Sayısı"
    )

    total_predictions = models.PositiveIntegerField(
        default=0, verbose_name="Toplam Tahmin Sayısı"
    )

    # Eğitim süresi (saniye)
    training_time_seconds = models.FloatField(
        default=0.0, verbose_name="Eğitim Süresi (saniye)"
    )

    # Model boyutu (byte)
    model_size_bytes = models.PositiveBigIntegerField(
        default=0, verbose_name="Model Boyutu (byte)"
    )

    # Ek veriler (hyperparameters, loss history, vb.)
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Ek Veriler")

    # Zaman damgası
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Kayıt Tarihi")

    class Meta:
        verbose_name = "Model Performansı"
        verbose_name_plural = "Model Performansları"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model_name", "timestamp"]),
            models.Index(fields=["accuracy"]),
            models.Index(fields=["timestamp"]),
        ]

        # En son performans kayıtları için unique constraint
        constraints = [
            models.UniqueConstraint(
                fields=["model_name", "model_version"],
                name="unique_model_version_performance",
            )
        ]

    def __str__(self):
        return f"{self.get_model_name_display()} v{self.model_version} - {self.accuracy:.2%}"

    @property
    def performance_grade(self):
        """Performans notu (A-F)"""
        if self.accuracy >= 0.95:
            return "A+"
        elif self.accuracy >= 0.90:
            return "A"
        elif self.accuracy >= 0.85:
            return "B+"
        elif self.accuracy >= 0.80:
            return "B"
        elif self.accuracy >= 0.75:
            return "C+"
        elif self.accuracy >= 0.70:
            return "C"
        elif self.accuracy >= 0.65:
            return "D"
        else:
            return "F"


class MLModelState(models.Model):
    """
    ML model durumları ve parametre kayıtları
    """

    model_name = models.CharField(max_length=50, unique=True, verbose_name="Model Adı")

    # Model durumu
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    is_training = models.BooleanField(default=False, verbose_name="Eğitim halinde mi?")

    # Model parametreleri (JSON formatında)
    parameters = models.JSONField(default=dict, verbose_name="Model Parametreleri")

    # Model ağırlıkları yolu
    weights_path = models.CharField(
        max_length=255, blank=True, verbose_name="Ağırlıklar Dosya Yolu"
    )

    # Son eğitim tarihi
    last_trained_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Son Eğitim Tarihi"
    )

    # Son güncelleme tarihi
    last_updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Son Güncelleme Tarihi"
    )

    # Oluşturulma tarihi
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Oluşturulma Tarihi"
    )

    class Meta:
        verbose_name = "ML Model Durumu"
        verbose_name_plural = "ML Model Durumları"
        ordering = ["model_name"]

    def __str__(self):
        status = "Aktif" if self.is_active else "Pasif"
        training = " (Eğitimde)" if self.is_training else ""
        return f"{self.model_name} - {status}{training}"


class ReinforcementLearningLog(models.Model):
    """
    Pekiştirmeli öğrenme işlem kayıtları
    """

    ACTION_TYPES = [
        ("assign_priority", "Öncelik Ataması"),
        ("assign_category", "Kategori Ataması"),
        ("estimate_resolution", "Çözüm Süresi Tahmini"),
        ("escalation_decision", "Yükseltme Kararı"),
        ("resource_allocation", "Kaynak Tahsisi"),
    ]

    # Episode bilgileri
    episode = models.PositiveIntegerField(verbose_name="Episode Numarası")

    step = models.PositiveIntegerField(verbose_name="Adım Numarası")

    # Durum, eylem, ödül
    state = models.JSONField(verbose_name="Durum (State)")

    action = models.CharField(
        max_length=30, choices=ACTION_TYPES, verbose_name="Eylem (Action)"
    )

    action_value = models.JSONField(default=dict, verbose_name="Eylem Değeri")

    reward = models.FloatField(verbose_name="Ödül (Reward)")

    next_state = models.JSONField(null=True, blank=True, verbose_name="Sonraki Durum")

    # Q-değeri
    q_value = models.FloatField(null=True, blank=True, verbose_name="Q-Değeri")

    # Keşif/sömürü bilgisi
    epsilon = models.FloatField(verbose_name="Epsilon Değeri")

    is_exploration = models.BooleanField(verbose_name="Keşif mi?")

    # İlgili şikayet
    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rl_logs",
        verbose_name="İlgili Şikayet",
    )

    # Zaman damgası
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zaman Damgası")

    class Meta:
        verbose_name = "RL İşlem Kaydı"
        verbose_name_plural = "RL İşlem Kayıtları"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["episode", "step"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["reward"]),
        ]

    def __str__(self):
        return f"Episode {self.episode}, Step {self.step} - {self.get_action_display()}"
