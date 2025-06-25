"""
Raporlama Modülü URL Yapılandırması
===================================

Bu dosya raporlama sistemi için URL rotalarını tanımlar.
Rapor oluşturma, görüntüleme, dışa aktarma işlemleri için endpoint'ler içerir.

URL Yapısı:
- /reports/ - Rapor listesi
- /reports/create/ - Yeni rapor oluşturma
- /reports/<id>/ - Rapor detayı
- /reports/<id>/update/ - Rapor güncelleme
- /reports/<id>/delete/ - Rapor silme
- /reports/export/pdf/ - PDF dışa aktarma
- /reports/export/excel/ - Excel dışa aktarma

Özellikler:
- PDF ve Excel formatında dışa aktarma
- Dinamik rapor oluşturma
- Filtreleme ve sıralama
- Çizelge ve grafik desteği
"""

from django.urls import path

from . import views

# Uygulama namespace'i - URL tersine çevirmede kullanılır
app_name = "reports"

# URL pattern'leri - raporlama sistemi için
urlpatterns = [
    # Ana rapor listesi - tüm raporları görüntüler
    path("", views.ReportListView.as_view(), name="report_list"),
    # PDF formatında rapor dışa aktarma
    path("export/pdf/", views.report_list_pdf, name="report_list_pdf"),
    # Excel formatında rapor dışa aktarma
    path("export/excel/", views.report_list_excel, name="report_list_excel"),
    # Yeni rapor oluşturma formu
    path("create/", views.ReportCreateView.as_view(), name="report_create"),
    # Rapor detay sayfası - ID ile erişim
    path("<int:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    # Rapor güncelleme formu
    path("<int:pk>/update/", views.ReportUpdateView.as_view(), name="report_update"),
    # Rapor silme onayı ve işlemi
    path("<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
]
