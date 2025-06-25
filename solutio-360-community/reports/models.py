from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from complaints.models import Complaint, ComplaintCategory
from core.models import BaseModel
from users.models import Department, User

# Ortak rapor sabitleri
REPORT_TYPES = (
    ("COMPLAINT", _("Complaint Report")),  # Şikayet raporu
    ("PERFORMANCE", _("Performance Report")),  # Performans raporu
    ("SATISFACTION", _("Satisfaction Report")),  # Memnuniyet raporu
    ("DEPARTMENT", _("Department Report")),  # Departman raporu
    ("CUSTOM", _("Custom Report")),  # Özel rapor
)

FORMAT_CHOICES = (
    ("PDF", "PDF"),
    ("EXCEL", "Excel"),
    ("CSV", "CSV"),
    ("JSON", "JSON"),
)


class ReportTemplate(BaseModel):
    """
    Rapor şablonları modeli.

    Önceden tanımlanmış rapor şablonları.
    Parametreler ile özelleştirilebilir.
    """

    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    template_file = models.FileField(_("template file"), upload_to="reports/templates/")
    report_type = models.CharField(
        _("report type"), max_length=20, choices=REPORT_TYPES
    )
    format = models.CharField(_("format"), max_length=10, choices=FORMAT_CHOICES)
    parameters = models.JSONField(_("parameters"), default=dict)
    is_active = models.BooleanField(_("is active"), default=True)
    version = models.PositiveIntegerField(_("version"), default=1)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_templates",
        verbose_name=_("created by"),
    )

    class Meta:
        verbose_name = _("report template")
        verbose_name_plural = _("report templates")
        ordering = ["-created_at"]
        unique_together = ["name", "version"]

    def __str__(self):
        """Şablon adı ve versiyonu."""
        return f"{self.name} v{self.version}"


class Report(BaseModel):
    """
    Ana rapor modeli.

    Sistem içindeki raporları temsil eder.
    Şablon kullanılarak veya özel olarak oluşturulabilir.
    Otomatik veya manuel olarak oluşturulabilir.
    """

    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    report_type = models.CharField(
        _("report type"), max_length=20, choices=REPORT_TYPES
    )
    format = models.CharField(
        _("format"), max_length=10, choices=FORMAT_CHOICES, default="PDF"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_reports",
        verbose_name=_("created by"),
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name=_("department"),
    )
    is_template = models.BooleanField(_("is template"), default=False)
    template = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reports",
        verbose_name=_("template"),
    )
    parameters = models.JSONField(_("parameters"), default=dict)
    schedule = models.ForeignKey(
        "ReportSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name=_("schedule"),
    )
    last_generated = models.DateTimeField(_("last generated"), null=True, blank=True)
    file = models.FileField(
        _("file"), upload_to="reports/%Y/%m/", null=True, blank=True
    )
    is_public = models.BooleanField(_("is public"), default=False)
    access_level = models.PositiveSmallIntegerField(
        _("access level"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name=_("İlişkili Şikayet"),
    )
    ml_analysis = models.JSONField(
        _("Makine Öğrenmesi Analiz Sonuçları"),
        default=dict,
        blank=True,
        help_text=_("Raporun makine öğrenmesi ile elde edilen analiz sonuçları"),
    )

    class Meta:
        verbose_name = _("report")
        verbose_name_plural = _("reports")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["report_type", "department"]),
            models.Index(fields=["created_by", "is_template"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Rapor detay sayfası URL'si."""
        from django.urls import reverse

        return reverse("reports:report-detail", args=[str(self.id)])


class ReportSchedule(BaseModel):
    """
    Rapor zamanlama modeli.

    Raporların otomatik olarak belirli aralıklarla oluşturulmasını sağlar.
    Cron ifadeleri ile esnek zamanlama yapılabilir.
    """

    FREQUENCY_CHOICES = (
        ("DAILY", _("Daily")),  # Günlük
        ("WEEKLY", _("Weekly")),  # Haftalık
        ("MONTHLY", _("Monthly")),  # Aylık
        ("QUARTERLY", _("Quarterly")),  # Üç aylık
        ("YEARLY", _("Yearly")),  # Yıllık
        ("CUSTOM", _("Custom")),  # Özel (cron ile)
    )

    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    frequency = models.CharField(
        _("frequency"), max_length=20, choices=FREQUENCY_CHOICES
    )
    cron_expression = models.CharField(_("cron expression"), max_length=100, blank=True)
    start_date = models.DateTimeField(_("start date"))
    end_date = models.DateTimeField(_("end date"), null=True, blank=True)
    is_active = models.BooleanField(_("is active"), default=True)
    recipients = models.ManyToManyField(
        User, related_name="report_schedules", verbose_name=_("recipients")
    )
    last_run = models.DateTimeField(_("last run"), null=True, blank=True)
    next_run = models.DateTimeField(_("next run"), null=True, blank=True)
    parameters = models.JSONField(_("parameters"), default=dict)

    class Meta:
        verbose_name = _("report schedule")
        verbose_name_plural = _("report schedules")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["frequency", "is_active"]),
            models.Index(fields=["next_run"]),
        ]

    def __str__(self):
        """Zamanlama adı ve sıklığı."""
        return f"{self.name} ({self.get_frequency_display()})"


class ReportLog(BaseModel):
    """
    Rapor oluşturma günlüğü modeli.

    Rapor oluşturma işlemlerinin loglarını tutar.
    Başarılı/başarısız durumları takip eder.
    """

    STATUS_CHOICES = (
        ("PENDING", _("Pending")),  # Bekliyor
        ("RUNNING", _("Running")),  # Çalışıyor
        ("COMPLETED", _("Completed")),  # Tamamlandı
        ("FAILED", _("Failed")),  # Başarısız
        ("CANCELLED", _("Cancelled")),  # İptal edildi
    )

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="logs", verbose_name=_("report")
    )
    status = models.CharField(_("status"), max_length=20, choices=STATUS_CHOICES)
    started_at = models.DateTimeField(_("started at"))
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)
    duration = models.DurationField(_("duration"), null=True, blank=True)
    error_message = models.TextField(_("error message"), blank=True)
    parameters = models.JSONField(_("parameters"), default=dict)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_report_logs",
        verbose_name=_("generated by"),
    )
    file_size = models.PositiveIntegerField(_("file size"), null=True, blank=True)
    file_path = models.CharField(_("file path"), max_length=500, blank=True)

    class Meta:
        verbose_name = _("report log")
        verbose_name_plural = _("report logs")
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["report", "status"]),
            models.Index(fields=["started_at", "completed_at"]),
        ]

    def __str__(self):
        """Log açıklaması."""
        return f"{self.report.name} - {self.get_status_display()}"


class Dashboard(BaseModel):
    """
    Dashboard modeli.

    Özelleştirilebilir dashboard'lar.
    Widget'lar ile zengin görünümler oluşturulabilir.
    """

    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    layout = models.JSONField(_("layout"), default=dict)
    is_public = models.BooleanField(_("is public"), default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_dashboards",
        verbose_name=_("created by"),
    )
    shared_with = models.ManyToManyField(
        User, related_name="shared_dashboards", verbose_name=_("shared with")
    )
    refresh_interval = models.PositiveIntegerField(_("refresh interval"), default=0)
    last_refresh = models.DateTimeField(_("last refresh"), null=True, blank=True)
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("dashboard")
        verbose_name_plural = _("dashboards")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by", "is_public"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Dashboard detay sayfası URL'si."""
        from django.urls import reverse

        return reverse("reports:dashboard-detail", args=[str(self.id)])


class DashboardWidget(BaseModel):
    """
    Dashboard widget modeli.

    Dashboard'larda gösterilecek widget'lar.
    Farklı türlerde veri görselleştirmeleri.
    """

    WIDGET_TYPES = (
        ("CHART", _("Chart")),  # Grafik
        ("TABLE", _("Table")),  # Tablo
        ("METRIC", _("Metric")),  # Metrik (sayı)
        ("LIST", _("List")),  # Liste
        ("CUSTOM", _("Custom")),  # Özel
    )

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name="widgets",
        verbose_name=_("dashboard"),
    )
    name = models.CharField(_("name"), max_length=200)
    widget_type = models.CharField(
        _("widget type"), max_length=20, choices=WIDGET_TYPES
    )
    data_source = models.CharField(_("data source"), max_length=200)
    configuration = models.JSONField(_("configuration"), default=dict)
    position = models.JSONField(_("position"), default=dict)
    size = models.JSONField(_("size"), default=dict)
    refresh_interval = models.PositiveIntegerField(_("refresh interval"), default=0)
    last_refresh = models.DateTimeField(_("last refresh"), null=True, blank=True)
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("dashboard widget")
        verbose_name_plural = _("dashboard widgets")
        ordering = ["position"]
        indexes = [
            models.Index(fields=["dashboard", "widget_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        """Widget adı ve türü."""
        return f"{self.name} ({self.get_widget_type_display()})"
