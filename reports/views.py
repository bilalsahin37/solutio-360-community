"""
Raporlama Modülü View'ları
=========================

Bu dosya raporlama sistemi için Django view'larını içerir.
Rapor oluşturma, görüntüleme, dışa aktarma ve yönetim işlemleri.

View Türleri:
- ListView: Rapor listesi ve istatistikler
- DetailView: Rapor detayları
- CreateView: Yeni rapor oluşturma
- UpdateView: Rapor güncelleme
- DeleteView: Rapor silme
- Function Views: PDF/Excel dışa aktarma

Özellikler:
- Aylık rapor istatistikleri
- Chart.js ile grafik desteği
- PDF ve Excel dışa aktarma
- Kullanıcı tabanlı yetkilendirme
"""

import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

import openpyxl  # Excel dosyası oluşturma kütüphanesi
from xhtml2pdf import pisa  # HTML'den PDF oluşturma kütüphanesi

from .models import Report

# Logging yapılandırması
logger = logging.getLogger(__name__)


class ReportListView(LoginRequiredMixin, ListView):
    """
    Rapor listesi view'ı.

    Tüm raporları listeler ve aylık istatistikler sunar.
    Chart.js ile görselleştirilmiş veriler içerir.

    Attributes:
        model: Report modeli
        template_name: Liste template'i
        context_object_name: Template değişken adı
        ordering: Sıralama kriteri (en yeni önce)

    Methods:
        get_context_data(): Ek context verileri ekler
    """

    model = Report  # Report modeli kullanılacak
    template_name = "reports/report_list.html"  # Liste template'i
    context_object_name = "reports"  # Template'de 'reports' değişkeni
    ordering = ["-created_at"]  # En yeni raporlar önce

    def get_context_data(self, **kwargs):
        """
        Template için ek context verileri hazırlar.

        Aylık rapor istatistikleri ve chart verileri ekler.

        Args:
            **kwargs: Üst sınıftan gelen context verileri

        Returns:
            dict: Genişletilmiş context verileri
        """
        context = super().get_context_data(**kwargs)
        reports = self.get_queryset()

        # Toplam rapor sayısı
        context["total_reports"] = reports.count()

        # Son 6 ayın rapor istatistikleri
        now = timezone.now()
        months = [
            (now.replace(day=1) - timezone.timedelta(days=30 * i)).strftime("%Y-%m")
            for i in range(5, -1, -1)  # 5 aydan geriye doğru
        ]

        # Her ay için rapor sayısını hesapla
        monthly_counts = []
        for m in months:
            y, mo = m.split("-")
            count = reports.filter(created_at__year=int(y), created_at__month=int(mo)).count()
            monthly_counts.append(count)

        # Chart.js için JSON formatında veri hazırla
        context["monthly_chart_data"] = json.dumps(
            {
                "labels": months,  # X ekseni etiketleri
                "datasets": [
                    {
                        "label": "Aylık Rapor Oluşturma",
                        "data": monthly_counts,  # Y ekseni verileri
                        "backgroundColor": "#60a5fa",  # Grafik rengi
                    }
                ],
            }
        )
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    """
    Rapor detay view'ı.

    Belirli bir raporun detay bilgilerini gösterir.
    Rapor içeriği, meta veriler ve işlem geçmişi.

    Attributes:
        model: Report modeli
        template_name: Detay template'i
        context_object_name: Template değişken adı
    """

    model = Report  # Report modeli
    template_name = "reports/report_detail.html"  # Detay template'i
    context_object_name = "report"  # Template'de 'report' değişkeni


class ReportCreateView(LoginRequiredMixin, CreateView):
    """
    Rapor oluşturma view'ı.

    Yeni rapor oluşturma formu.
    Kullanıcı otomatik olarak created_by alanına atanır.

    Attributes:
        model: Report modeli
        template_name: Form template'i
        fields: Form alanları listesi
        success_url: Başarılı kayıt sonrası yönlendirme

    Methods:
        form_valid(): Form geçerli olduğunda çalışır
    """

    model = Report  # Report modeli
    template_name = "reports/report_form.html"  # Form template'i

    # Form alanları - kullanıcı tarafından doldurulabilir
    fields = [
        "name",  # Rapor adı
        "description",  # Rapor açıklaması
        "report_type",  # Rapor türü
        "format",  # Rapor formatı
        "department",  # İlgili departman
        "is_template",  # Şablon mu?
        "template",  # Kullanılan şablon
        "parameters",  # Rapor parametreleri
        "schedule",  # Zamanlama bilgisi
        "file",  # Rapor dosyası
        "is_public",  # Herkese açık mı?
        "access_level",  # Erişim seviyesi
    ]

    # Başarılı kayıt sonrası rapor listesine yönlendir
    success_url = reverse_lazy("reports:report_list")

    def form_valid(self, form):
        """
        Form geçerli olduğunda çalışır.

        Raporu oluşturan kullanıcıyı otomatik olarak atar.

        Args:
            form: Geçerli form nesnesi

        Returns:
            HttpResponse: Üst sınıfın form_valid sonucu
        """
        # Raporu oluşturan kullanıcıyı ata
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ReportUpdateView(LoginRequiredMixin, UpdateView):
    """
    Rapor güncelleme view'ı.

    Mevcut raporu güncelleme formu.
    Sadece raporu oluşturan kullanıcı güncelleyebilir.

    Attributes:
        model: Report modeli
        template_name: Form template'i
        fields: Güncellenebilir alanlar
        success_url: Başarılı güncelleme sonrası yönlendirme

    Methods:
        get_queryset(): Sadece kullanıcının raporlarını döndürür
    """

    model = Report  # Report modeli
    template_name = "reports/report_form.html"  # Form template'i

    # Güncellenebilir alanlar
    fields = [
        "name",  # Rapor adı
        "description",  # Rapor açıklaması
        "report_type",  # Rapor türü
        "format",  # Rapor formatı
        "department",  # İlgili departman
        "is_template",  # Şablon mu?
        "template",  # Kullanılan şablon
        "parameters",  # Rapor parametreleri
        "schedule",  # Zamanlama bilgisi
        "file",  # Rapor dosyası
        "is_public",  # Herkese açık mı?
        "access_level",  # Erişim seviyesi
    ]

    # Güncelleme sonrası rapor listesine yönlendir
    success_url = reverse_lazy("reports:report_list")

    def get_queryset(self):
        """
        Sadece kullanıcının kendi raporlarını döndürür.

        Returns:
            QuerySet: Kullanıcının oluşturduğu raporlar
        """
        return super().get_queryset().filter(created_by=self.request.user)


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """
    Rapor silme view'ı.

    Rapor silme onay sayfası.
    Sadece raporu oluşturan kullanıcı silebilir.

    Attributes:
        model: Report modeli
        template_name: Onay template'i
        success_url: Silme sonrası yönlendirme

    Methods:
        get_queryset(): Sadece kullanıcının raporlarını döndürür
    """

    model = Report  # Report modeli
    template_name = "reports/report_confirm_delete.html"  # Onay template'i

    # Silme sonrası rapor listesine yönlendir
    success_url = reverse_lazy("reports:report_list")

    def get_queryset(self):
        """
        Sadece kullanıcının kendi raporlarını döndürür.

        Returns:
            QuerySet: Kullanıcının oluşturduğu raporlar
        """
        return super().get_queryset().filter(created_by=self.request.user)


def report_list_pdf(request):
    """
    Rapor listesini PDF formatında dışa aktarır.

    xhtml2pdf kütüphanesini kullanarak HTML'den PDF oluşturur.
    Tüm raporları içeren bir PDF dosyası döndürür.

    Args:
        request: HTTP isteği

    Returns:
        HttpResponse: PDF dosyası veya hata mesajı
    """
    try:
        # Tüm raporları al
        reports = Report.objects.all()

        # HTML template'ini render et
        html = render_to_string("reports/report_list_pdf.html", {"reports": reports})

        # PDF response oluştur
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=raporlar.pdf"

        # HTML'den PDF oluştur
        pisa_status = pisa.CreatePDF(html, dest=response)

        # Hata kontrolü
        if pisa_status.err:
            logger.error("PDF oluşturma hatası: %s", pisa_status.err)
            return HttpResponse("PDF oluşturulurken bir hata oluştu", status=500)

        return response

    except Exception as e:
        # Beklenmeyen hata durumu
        logger.error("PDF dışa aktarma hatası: %s", str(e))
        return HttpResponse(f"PDF oluşturulurken bir hata oluştu: {str(e)}", status=500)


def report_list_excel(request):
    """
    Rapor listesini Excel formatında dışa aktarır.

    openpyxl kütüphanesini kullanarak Excel dosyası oluşturur.
    Rapor başlığı, türü, durumu ve oluşturulma tarihini içerir.

    Args:
        request: HTTP isteği

    Returns:
        HttpResponse: Excel dosyası veya hata mesajı
    """
    try:
        # Tüm raporları al
        reports = Report.objects.all()

        # Excel workbook oluştur
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Raporlar"  # Sayfa başlığı

        # Başlık satırını ekle
        headers = ["Başlık", "Tip", "Durum", "Oluşturulma"]
        ws.append(headers)

        # Rapor verilerini ekle
        for r in reports:
            row_data = [
                r.title,  # Rapor başlığı
                str(r.template.template_type) if r.template else "N/A",  # Rapor türü
                str(r.status),  # Rapor durumu
                r.created_at.strftime("%d.%m.%Y %H:%M"),  # Oluşturulma tarihi
            ]
            ws.append(row_data)

        # Excel response oluştur
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=raporlar.xlsx"

        # Excel dosyasını response'a kaydet
        wb.save(response)
        return response

    except Exception as e:
        # Beklenmeyen hata durumu
        logger.error("Excel dışa aktarma hatası: %s", str(e))
        return HttpResponse(f"Excel dosyası oluşturulurken bir hata oluştu: {str(e)}", status=500)
