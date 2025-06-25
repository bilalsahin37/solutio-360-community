# -*- coding: utf-8 -*-
"""
Şikayet Yönetimi View'ları - Solutio 360 PWA
============================================

Bu modül şikayet yönetim sistemi için Django view'larını içerir.
Modern PWA uyumlu kullanıcı arayüzü ile entegre çalışır.

Ana Özellikler:
- Şikayet listesi ve filtreleme sistemi
- Şikayet detay görüntüleme ve yorum sistemi
- Şikayet oluşturma ve güncelleme
- Makine öğrenmesi tabanlı metin analizi
- Çoklu dosya yükleme sistemi
- AJAX tabanlı dinamik işlemler
- Rol tabanlı erişim kontrolü

View Türleri:
- Class-based Views (CBV): CRUD işlemleri
- Function-based Views (FBV): Özel işlemler
- AJAX Views: Dinamik veri işleme

Güvenlik Özellikleri:
- Login gereksinimi
- Kullanıcı yetki kontrolü
- CSRF koruması
- Dosya yükleme güvenliği
"""

import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import models as django_models
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import CommentForm, ComplaintForm
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
    analyze_complaint_text,
)

# Loglama konfigürasyonu - hata ve bilgi mesajları için
logger = logging.getLogger(__name__)

# Django'nun kullanıcı modelini al
User = get_user_model()

# Create your views here.


class ComplaintListView(LoginRequiredMixin, ListView):
    """
    Şikayet Listesi View'ı
    =====================

    Şikayetleri listeleyen ve filtreleme imkanı sunan ana view.
    Kullanıcı rolüne göre farklı şikayetleri gösterir.

    Özellikler:
    - Admin: Tüm şikayetleri görür
    - Normal kullanıcı: Sadece kendi şikayetlerini görür
    - Çoklu filtreleme sistemi (kategori, durum, öncelik, etiket)
    - Sayfalama (pagination) desteği
    - Performans optimizasyonu (select_related)

    Filtreler:
    - Kategori: Şikayet kategorilerine göre
    - Durum: Şikayet durumuna göre (taslak, gönderildi, vs.)
    - Öncelik: Aciliyet seviyesine göre
    - Etiketler: Şikayet etiketlerine göre
    - Kurumlar: Şikayet edilen kurumlara göre
    - Birimler: Şikayet edilen birimlere göre
    - Alt birimler: Şikayet edilen alt birimlere göre
    - Kişiler: Şikayet edilen kişilere göre
    """

    model = Complaint  # Şikayet modeli kullanılacak
    template_name = "complaints/complaint_list_new.html"  # Liste template'i
    context_object_name = "complaints"  # Template'de kullanılacak değişken adı
    ordering = ["-created_at"]  # En yeni şikayetler önce gelsin
    paginate_by = 20  # Sayfa başına 20 şikayet göster

    def get_queryset(self):
        """
        Şikayet listesini hazırlar ve filtreler.

        Kullanıcı rolüne göre farklı şikayetleri döndürür:
        - Admin kullanıcılar: Tüm şikayetleri görebilir
        - Normal kullanıcılar: Sadece kendi şikayetlerini görebilir

        URL parametrelerine göre filtreleme yapar:
        - ?category=1,2,3 (çoklu kategori seçimi)
        - ?status=1,2 (çoklu durum seçimi)
        - ?priority=1,2 (çoklu öncelik seçimi)
        - ?tags=1,2,3 (çoklu etiket seçimi)

        Returns:
            QuerySet: Filtrelenmiş şikayet listesi
        """
        # DRAFT durumundaki şikayetleri otomatik olarak SUBMITTED yap
        draft_complaints = Complaint.objects.filter(status="DRAFT")
        if draft_complaints.exists():
            updated_count = draft_complaints.update(status="SUBMITTED")
            print(f"DEBUG: {updated_count} DRAFT şikayet SUBMITTED yapıldı")

        # Kullanıcı yetkisine göre temel sorgu oluştur
        if self.request.user.is_staff:
            # Admin kullanıcılar tüm şikayetleri görebilir
            qs = Complaint.objects.all()
        else:
            # Normal kullanıcılar sadece kendi şikayetlerini görebilir
            qs = Complaint.objects.filter(submitter=self.request.user)

        # Performans optimizasyonu: kategori bilgilerini tek sorguda al
        qs = qs.select_related("category")

        # URL parametrelerini al
        GET = self.request.GET

        # Çoklu kategori filtresi
        if GET.getlist("category"):
            qs = qs.filter(category_id__in=GET.getlist("category"))

        # Çoklu durum filtresi
        if GET.getlist("status"):
            qs = qs.filter(status_id__in=GET.getlist("status"))

        # Çoklu öncelik filtresi
        if GET.getlist("priority"):
            qs = qs.filter(priority_id__in=GET.getlist("priority"))

        # Çoklu etiket filtresi (many-to-many ilişki)
        if GET.getlist("tags"):
            qs = qs.filter(tags__in=GET.getlist("tags")).distinct()

        # Şikayet edilen kurumlar filtresi
        if GET.getlist("complained_institutions"):
            qs = qs.filter(
                complained_institutions__in=GET.getlist("complained_institutions")
            ).distinct()

        # Şikayet edilen birimler filtresi
        if GET.getlist("complained_units"):
            qs = qs.filter(
                complained_units__in=GET.getlist("complained_units")
            ).distinct()

        # Şikayet edilen alt birimler filtresi
        if GET.getlist("complained_subunits"):
            qs = qs.filter(
                complained_subunits__in=GET.getlist("complained_subunits")
            ).distinct()

        # Şikayet edilen kişiler filtresi
        if GET.getlist("complained_people"):
            qs = qs.filter(
                complained_people__in=GET.getlist("complained_people")
            ).distinct()

        # Tekrarlanan kayıtları temizle ve döndür
        return qs.distinct()

    def get_context_data(self, **kwargs):
        """
        Template için ek veriler hazırlar.

        Filtre seçenekleri ve mevcut seçimleri template'e gönderir.
        Bu sayede kullanıcı hangi filtreleri seçtiğini görebilir.

        Args:
            **kwargs: Üst sınıftan gelen context verileri

        Returns:
            dict: Genişletilmiş context verileri
        """
        context = super().get_context_data(**kwargs)

        # Filtre seçenekleri - sadece aktif olanlar
        context["categories"] = ComplaintCategory.objects.filter(is_active=True)
        context["statuses"] = Status.objects.filter(is_active=True)
        context["priorities"] = Priority.objects.filter(is_active=True)
        context["tags"] = ComplaintTag.objects.all()
        context["institutions"] = Institution.objects.all()
        context["units"] = Unit.objects.all()
        context["subunits"] = Subunit.objects.all()
        context["people"] = Person.objects.all()

        # Mevcut seçimleri template'e gönder
        GET = self.request.GET
        context["selected_categories"] = GET.getlist("category")
        context["selected_statuses"] = GET.getlist("status")
        context["selected_priorities"] = GET.getlist("priority")
        context["selected_tags"] = GET.getlist("tags")
        context["selected_institutions"] = GET.getlist("complained_institutions")
        context["selected_units"] = GET.getlist("complained_units")
        context["selected_subunits"] = GET.getlist("complained_subunits")
        context["selected_people"] = GET.getlist("complained_people")

        return context


class ComplaintDetailView(LoginRequiredMixin, DetailView):
    """
    Şikayet Detay View'ı
    ===================

    Belirli bir şikayetin detay bilgilerini gösterir.
    Şikayet içeriği, yorumlar, ekler ve durum geçmişi.

    Özellikler:
    - Şikayet detay bilgileri
    - Tüm yorumlar (tarih sırasına göre)
    - Yeni yorum ekleme formu
    - Durum değiştirme seçenekleri
    - Dosya ekleri görüntüleme
    """

    model = Complaint  # Şikayet modeli
    template_name = "complaints/complaint_detail.html"  # Detay template'i
    context_object_name = "complaint"  # Template'de kullanılacak değişken adı

    def get_context_data(self, **kwargs):
        """
        Şikayet detayı için ek veriler hazırlar.

        Yorumlar, yorum formu ve durum seçeneklerini ekler.

        Args:
            **kwargs: Üst sınıftan gelen context verileri

        Returns:
            dict: Genişletilmiş context verileri
        """
        context = super().get_context_data(**kwargs)

        # Şikayete ait tüm yorumları tarih sırasına göre getir
        context["comments"] = self.object.comments.all().order_by("created_at")

        # Yeni yorum ekleme formu
        context["comment_form"] = CommentForm()

        # Durum değiştirme için aktif durumlar
        context["statuses"] = Status.objects.filter(is_active=True)

        return context


@login_required
def complaint_create(request):
    """
    Şikayet Oluşturma View'ı (Function-based)
    ========================================

    Yeni şikayet oluşturma işlemini yönetir.
    Form doğrulama, dosya yükleme ve ML analizi yapar.

    Özellikler:
    - Şikayet formu işleme
    - Çoklu dosya yükleme
    - Etiket oluşturma ve atama
    - Makine öğrenmesi analizi
    - Many-to-many ilişki yönetimi

    İşlem Adımları:
    1. Form doğrulama
    2. Şikayet kaydı oluşturma
    3. Etiketleri işleme ve atama
    4. Dosyaları yükleme ve kaydetme
    5. ML analizi yapma
    6. Başarı mesajı ve yönlendirme

    Args:
        request: HTTP request nesnesi

    Returns:
        HttpResponse: Form sayfası veya yönlendirme
    """
    if request.method == "POST":
        # POST isteği - form gönderildi
        post_data = request.POST.copy()

        # Etiketler: Tagify bileşeninden gelen string'i işle
        # Format: "etiket1,etiket2,etiket3" veya tab ile ayrılmış
        tags_val = post_data.get("tags", "")
        tag_names = [
            t.strip() for t in tags_val.replace("\t", ",").split(",") if t.strip()
        ]

        # Form oluştur ve doğrula
        form = ComplaintForm(post_data, request.FILES)

        if form.is_valid():
            # Form geçerli - şikayeti kaydet
            complaint = form.save(commit=False)  # Henüz veritabanına kaydetme
            complaint.submitter = request.user  # Şikayet sahibini ata
            complaint.status = "SUBMITTED"  # Durumu gönderildi yap
            complaint.save()  # Şimdi veritabanına kaydet

            # Etiketleri işle ve many-to-many ilişki kur
            tag_objs = []
            for tag in tag_names:
                # Etiket varsa getir, yoksa oluştur
                obj, created = ComplaintTag.objects.get_or_create(name=tag)
                tag_objs.append(obj)

            # Etiketleri şikayete ata
            complaint.tags.set(tag_objs)

            # Many-to-many ilişkileri kaydet
            form.save_m2m()

            # Çoklu dosya yükleme işlemi
            files = request.FILES.getlist("attachments")
            for f in files:
                # Her dosya için ek kaydı oluştur
                ComplaintAttachment.objects.create(
                    complaint=complaint,  # Şikayet ilişkisi
                    file=f,  # Dosya
                    filename=f.name,  # Dosya adı
                    file_type=f.content_type,  # MIME tipi
                    file_size=f.size,  # Dosya boyutu
                )

            # Makine öğrenmesi analizi yap
            ml_result = analyze_complaint_text(complaint.description)
            complaint.ml_analysis = ml_result
            complaint.save(update_fields=["ml_analysis"])

            # Başarı mesajı ve ana sayfaya yönlendirme
            messages.success(request, "Şikayetiniz başarıyla oluşturuldu.")
            return redirect("dashboard")
    else:
        # GET isteği - boş form göster
        form = ComplaintForm()

    # Form sayfasını render et
    return render(request, "complaints/complaint_form.html", {"form": form})


class ComplaintUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Şikayet Güncelleme View'ı
    =========================

    Mevcut şikayeti güncelleme işlemi.
    Sadece şikayet sahibi güncelleyebilir.

    Güvenlik:
    - LoginRequiredMixin: Giriş yapmış olma zorunluluğu
    - UserPassesTestMixin: Kullanıcı yetki kontrolü

    Özellikler:
    - Şikayet güncelleme formu
    - Yetki kontrolü
    - Çoklu alan desteği
    """

    model = Complaint  # Şikayet modeli
    form_class = ComplaintForm  # Kullanılacak form sınıfı
    template_name = "complaints/complaint_form.html"  # Form template'i
    success_url = reverse_lazy(
        "complaints:complaint_list"
    )  # Başarı sonrası yönlendirme

    def test_func(self):
        """
        Kullanıcı yetki kontrolü.

        Sadece şikayet sahibi güncelleyebilir.

        Returns:
            bool: Yetki var mı?
        """
        complaint = self.get_object()
        return complaint.submitter == self.request.user

    def form_valid(self, form):
        """
        Geçerli form işlemi.

        Şikayet sahibini tekrar atar ve kaydeder.

        Args:
            form: Geçerli form nesnesi

        Returns:
            HttpResponse: Üst sınıfın form_valid sonucu
        """
        # Form'u kaydet ama henüz veritabanına yazma
        complaint = form.save(commit=False)

        # Mevcut şikayetin verilerini koru
        original_complaint = self.get_object()
        complaint.submitter = original_complaint.submitter
        complaint.created_at = original_complaint.created_at
        complaint.updated_at = timezone.now()

        # Şikayeti kaydet
        complaint.save()

        # Many-to-many ilişkileri kaydet
        form.save_m2m()

        # Başarı mesajı
        messages.success(self.request, "Şikayet başarıyla güncellendi.")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Form için ek context verileri.

        Çoklu seçim alanlarını belirtir.

        Args:
            **kwargs: Üst sınıftan gelen context

        Returns:
            dict: Genişletilmiş context
        """
        context = super().get_context_data(**kwargs)

        # Çoklu seçim alanları - JavaScript için
        context["multi_fields"] = [
            "complained_institutions",  # Şikayet edilen kurumlar
            "complained_units",  # Şikayet edilen birimler
            "complained_subunits",  # Şikayet edilen alt birimler
            "complained_people",  # Şikayet edilen kişiler
            "tags",  # Etiketler
            "reviewers",  # Değerlendiriciler
            "inspectors",  # Denetçiler
        ]
        return context


class ComplaintDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Şikayet Silme View'ı
    ===================

    Şikayet silme onay sayfası ve işlemi.
    Sadece şikayet sahibi silebilir.

    Güvenlik:
    - Giriş yapmış kullanıcı zorunluluğu
    - Şikayet sahibi kontrolü
    - Onay sayfası
    """

    model = Complaint  # Şikayet modeli
    template_name = "complaints/complaint_confirm_delete.html"  # Onay template'i
    success_url = reverse_lazy("complaints:complaint_list")  # Silme sonrası yönlendirme

    def test_func(self):
        """
        Kullanıcı yetki kontrolü.

        Sadece şikayet sahibi silebilir.

        Returns:
            bool: Silme yetkisi var mı?
        """
        complaint = self.get_object()
        return complaint.submitter == self.request.user

    def post(self, request, *args, **kwargs):
        """
        POST request ile direkt silme işlemi
        """
        complaint = self.get_object()
        complaint_title = complaint.title

        # Silme işlemini gerçekleştir
        complaint.delete()

        # Başarı mesajı
        messages.success(
            request, f"'{complaint_title}' başlıklı şikayet başarıyla silindi."
        )

        # Referer kontrolü - listeden geliyorsa listeye dön
        referer = request.META.get("HTTP_REFERER", "")
        if (
            "complaints/" in referer
            and "/complaints/" + str(kwargs.get("pk")) not in referer
        ):
            return redirect("complaints:complaint_list")
        else:
            return redirect("complaints:complaint_list")


class AddCommentView(LoginRequiredMixin, View):
    """
    Yorum Ekleme View'ı
    ==================

    Şikayete yorum ekleme işlemi.
    POST isteği ile çalışır.

    Özellikler:
    - Yorum formu işleme
    - Dosya eki desteği
    - Başarı/hata mesajları
    - Şikayet detayına yönlendirme
    """

    def post(self, request, pk):
        """
        Yorum ekleme POST işlemi.

        Args:
            request: HTTP request nesnesi
            pk: Şikayet ID'si

        Returns:
            HttpResponse: Şikayet detayına yönlendirme
        """
        # Şikayeti bul veya 404 hatası ver
        complaint = get_object_or_404(Complaint, pk=pk)

        # Yorum formunu oluştur ve doğrula
        form = CommentForm(request.POST, request.FILES)

        if form.is_valid():
            # Form geçerli - yorumu kaydet
            comment = form.save(commit=False)
            comment.complaint = complaint  # Şikayet ilişkisi
            comment.sender = request.user  # Yorum gönderen
            comment.save()

            # Başarı mesajı
            messages.success(request, "Yorumunuz eklendi.")
        else:
            # Form geçersiz - hata mesajı
            messages.error(request, "Yorum eklenemedi.")

        # Şikayet detayına geri dön
        return redirect("complaints:complaint_detail", pk=pk)


class UpdateStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Durum Güncelleme View'ı
    ======================

    Şikayet durumunu güncelleme işlemi.
    Yetkili kullanıcılar için.

    Özellikler:
    - Durum değiştirme
    - Yetki kontrolü
    - Durum geçmişi
    - Bildirim sistemi
    """

    def test_func(self):
        """
        Durum değiştirme yetkisi kontrolü.

        Sadece yetkili personel durum değiştirebilir.

        Returns:
            bool: Durum değiştirme yetkisi var mı?
        """
        return self.request.user.is_staff

    def post(self, request, pk):
        """
        Durum güncelleme POST işlemi.

        Args:
            request: HTTP request nesnesi
            pk: Şikayet ID'si

        Returns:
            HttpResponse: Şikayet detayına yönlendirme
        """
        # Şikayeti bul
        complaint = get_object_or_404(Complaint, pk=pk)

        # Yeni durum ID'sini al
        new_status_id = request.POST.get("status")

        if new_status_id:
            # Yeni durumu bul
            new_status = get_object_or_404(Status, id=new_status_id)

            # Eski durumu kaydet (log için)
            old_status = complaint.status

            # Durumu güncelle
            complaint.status = new_status
            complaint.save()

            # Başarı mesajı
            messages.success(request, "Durum güncellendi.")

            # TODO: Durum değişikliği bildirimi gönder
            # TODO: Durum geçmişini kaydet

        # Şikayet detayına geri dön
        return redirect("complaints:complaint_detail", pk=pk)


class ReviewerComplaintListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Complaint
    template_name = "complaints/reviewer_panel.html"
    context_object_name = "complaints"
    paginate_by = 20

    def test_func(self):
        # Sadece yetkili personel erişebilir (is_staff kontrolü yeterli)
        return self.request.user.is_authenticated and self.request.user.is_staff

    def get_queryset(self):
        user = self.request.user
        # Staff kullanıcıları tüm şikayetleri görebilir
        if user.is_staff:
            qs = Complaint.objects.all()
        else:
            # Normal kullanıcılar sadece kendilerine atanmış şikayetleri görür
            qs = Complaint.objects.filter(assigned_to=user)

        # Filtreleme opsiyonları
        GET = self.request.GET
        status = GET.get("status", "").strip()
        if status:
            qs = qs.filter(status=status)

        priority = GET.get("priority", "").strip()
        if priority:
            qs = qs.filter(priority=priority)

        search = GET.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(submitter__first_name__icontains=search)
                | Q(submitter__last_name__icontains=search)
            )

        return qs.select_related("submitter", "category", "assigned_to").order_by(
            "-created_at"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ml_enabled"] = True
        context["total_complaints"] = Complaint.objects.count()
        context["pending_complaints"] = Complaint.objects.filter(
            status__in=["SUBMITTED", "IN_REVIEW"]
        ).count()
        context["resolved_complaints"] = Complaint.objects.filter(
            status="RESOLVED"
        ).count()
        context["my_assigned"] = Complaint.objects.filter(
            assigned_to=self.request.user
        ).count()

        # Filtreleme için seçenekler
        context["status_choices"] = Complaint.STATUS_CHOICES
        context["priority_choices"] = Complaint.PRIORITY_CHOICES

        return context


class InspectorComplaintListView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = "complaints/inspector_complaint_list.html"
    context_object_name = "complaints"
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Complaint.objects.filter(inspectors=self.request.user)
        qs = qs.select_related("category")
        GET = self.request.GET
        if GET.getlist("category"):
            qs = qs.filter(category_id__in=GET.getlist("category"))
        if GET.getlist("status"):
            qs = qs.filter(status_id__in=GET.getlist("status"))
        if GET.getlist("priority"):
            qs = qs.filter(priority_id__in=GET.getlist("priority"))
        if GET.getlist("tags"):
            qs = qs.filter(tags__in=GET.getlist("tags")).distinct()
        if GET.getlist("complained_institutions"):
            qs = qs.filter(
                complained_institutions__in=GET.getlist("complained_institutions")
            ).distinct()
        if GET.getlist("complained_units"):
            qs = qs.filter(
                complained_units__in=GET.getlist("complained_units")
            ).distinct()
        if GET.getlist("complained_subunits"):
            qs = qs.filter(
                complained_subunits__in=GET.getlist("complained_subunits")
            ).distinct()
        if GET.getlist("complained_people"):
            qs = qs.filter(
                complained_people__in=GET.getlist("complained_people")
            ).distinct()
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ComplaintCategory.objects.filter(is_active=True)
        context["statuses"] = Status.objects.filter(is_active=True)
        context["priorities"] = Priority.objects.filter(is_active=True)
        context["tags"] = ComplaintTag.objects.all()
        context["institutions"] = Institution.objects.all()
        context["units"] = Unit.objects.all()
        context["subunits"] = Subunit.objects.all()
        context["people"] = Person.objects.all()
        GET = self.request.GET
        context["selected_categories"] = GET.getlist("category")
        context["selected_statuses"] = GET.getlist("status")
        context["selected_priorities"] = GET.getlist("priority")
        context["selected_tags"] = GET.getlist("tags")
        context["selected_institutions"] = GET.getlist("complained_institutions")
        context["selected_units"] = GET.getlist("complained_units")
        context["selected_subunits"] = GET.getlist("complained_subunits")
        context["selected_people"] = GET.getlist("complained_people")
        return context


@csrf_exempt
def ajax_add_institution(request):
    if request.method == "POST" and request.user.is_authenticated:
        name = request.POST.get("name")
        if name:
            obj, created = Institution.objects.get_or_create(name=name)
            return JsonResponse({"id": obj.id, "name": obj.name, "created": created})
    return JsonResponse({"error": "Invalid"}, status=400)


@csrf_exempt
def ajax_add_unit(request):
    if request.method == "POST" and request.user.is_authenticated:
        name = request.POST.get("name")
        institution_id = request.POST.get("institution")
        if name and institution_id:
            inst = Institution.objects.filter(id=institution_id).first()
            if inst:
                obj, created = Unit.objects.get_or_create(name=name, institution=inst)
                return JsonResponse(
                    {"id": obj.id, "name": obj.name, "created": created}
                )
    return JsonResponse({"error": "Invalid"}, status=400)


@csrf_exempt
def ajax_add_subunit(request):
    if request.method == "POST" and request.user.is_authenticated:
        name = request.POST.get("name")
        unit_id = request.POST.get("unit")
        if name and unit_id:
            unit = Unit.objects.filter(id=unit_id).first()
            if unit:
                from .models import Subunit

                obj, created = Subunit.objects.get_or_create(name=name, unit=unit)
                return JsonResponse(
                    {"id": obj.id, "name": obj.name, "created": created}
                )
    return JsonResponse({"error": "Invalid"}, status=400)


@csrf_exempt
def ajax_add_person(request):
    if request.method == "POST" and request.user.is_authenticated:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        subunit_id = request.POST.get("subunit")
        if first_name and last_name and subunit_id:
            from .models import Subunit

            subunit = Subunit.objects.filter(id=subunit_id).first()
            if subunit:
                obj, created = Person.objects.get_or_create(
                    first_name=first_name, last_name=last_name, subunit=subunit
                )
                return JsonResponse(
                    {
                        "id": obj.id,
                        "name": f"{obj.first_name} {obj.last_name}",
                        "created": created,
                    }
                )
    return JsonResponse({"error": "Invalid"}, status=400)


@csrf_exempt
def ajax_add_tag(request):
    if request.method == "POST" and request.user.is_authenticated:
        name = request.POST.get("name")
        if name:
            obj, created = ComplaintTag.objects.get_or_create(name=name)
            return JsonResponse({"id": obj.id, "name": obj.name, "created": created})
    return JsonResponse({"error": "Invalid"}, status=400)


@csrf_exempt
def ajax_add_user(request):
    if request.method == "POST" and request.user.is_authenticated:
        username = request.POST.get("username")
        if username:
            User = get_user_model()
            obj = User.objects.filter(username=username).first()
            if obj:
                return JsonResponse(
                    {
                        "id": obj.id,
                        "name": obj.get_full_name() or obj.username,
                        "created": False,
                    }
                )
    return JsonResponse({"error": "Invalid"}, status=400)


@login_required
@require_POST
def withdraw_complaint(request, pk):
    """
    Şikayeti geri çekme view'ı
    """
    complaint = get_object_or_404(Complaint, pk=pk)

    # Sadece şikayet sahibi geri çekebilir
    if complaint.submitter != request.user:
        print(f"DEBUG - Permission denied: {complaint.submitter} != {request.user}")
        return HttpResponseForbidden("Bu şikayeti geri çekme yetkiniz yok.")

    # Geri çekilebilir mi kontrol et
    if not complaint.can_withdraw:
        print(f"DEBUG - Cannot withdraw: can_withdraw = {complaint.can_withdraw}")
        messages.error(request, "Bu şikayet geri çekilemez.")
        return redirect("complaints:complaint_detail", pk=pk)

    # Geri çekme sebebini al
    withdrawal_reason = request.POST.get("withdrawal_reason", "")
    print(f"DEBUG - Withdrawal reason: {withdrawal_reason}")

    try:
        old_status = complaint.status
        complaint.withdraw(reason=withdrawal_reason, user=request.user)
        print(f"DEBUG - Withdraw successful: {old_status} -> {complaint.status}")
        messages.success(request, "Şikayetiniz başarıyla geri çekildi.")

        # Bildirim gönder
        from complaints.models import ComplaintNotification

        ComplaintNotification.objects.create(
            complaint=complaint,
            recipient=request.user,
            notification_type="STATUS_CHANGE",
            message=f"'{complaint.title}' başlıklı şikayetiniz geri çekildi.",
        )

    except ValueError as e:
        print(f"DEBUG - Withdraw failed: {str(e)}")
        messages.error(request, str(e))

    # Referer'dan geldiği sayfayı kontrol et
    referer = request.META.get("HTTP_REFERER", "")
    if "/complaints/" in referer and not f"/complaints/{pk}/" in referer:
        return redirect("complaints:complaint_list")
    else:
        return redirect("complaints:complaint_detail", pk=pk)


@login_required
@require_POST
def cancel_complaint(request, pk):
    """
    Şikayeti iptal etme view'ı (admin yetkisi gerekir)
    """
    complaint = get_object_or_404(Complaint, pk=pk)

    # Sadece admin veya yetkili kullanıcılar iptal edebilir
    if not (
        request.user.is_staff or request.user.has_perm("complaints.change_complaint")
    ):
        return HttpResponseForbidden("Bu işlem için yetkiniz yok.")

    # İptal sebebini al
    cancellation_reason = request.POST.get("cancellation_reason", "")

    try:
        complaint.cancel(reason=cancellation_reason, user=request.user)
        messages.success(request, "Şikayet başarıyla iptal edildi.")

        # Şikayet sahibine bildirim gönder
        from complaints.models import ComplaintNotification

        ComplaintNotification.objects.create(
            complaint=complaint,
            recipient=complaint.submitter,
            notification_type="STATUS_CHANGE",
            message=f"'{complaint.title}' başlıklı şikayetiniz iptal edildi. Sebep: {cancellation_reason}",
        )

    except Exception as e:
        messages.error(request, f"İptal işlemi başarısız: {str(e)}")

    return redirect("complaints:complaint_detail", pk=pk)


@login_required
def delete_complaint(request, pk):
    """
    Şikayeti tamamen silme view'ı (sadece draft durumundakiler)
    """
    complaint = get_object_or_404(Complaint, pk=pk)

    # Sadece şikayet sahibi silebilir
    if complaint.submitter != request.user:
        return HttpResponseForbidden("Bu şikayeti silme yetkiniz yok.")

    # Sadece DRAFT durumundaki şikayetler silinebilir
    if complaint.status != "DRAFT":
        messages.error(request, "Sadece taslak durumundaki şikayetler silinebilir.")
        return redirect("complaints:complaint_detail", pk=pk)

    if request.method == "POST":
        title = complaint.title
        complaint.delete()
        messages.success(request, f"'{title}' başlıklı şikayet başarıyla silindi.")
        return redirect("complaints:complaint_list")

    return render(request, "complaints/confirm_delete.html", {"complaint": complaint})


@login_required
def export_complaints_excel(request):
    """
    Şikayetleri Excel formatında export eder
    """
    import csv

    from django.http import HttpResponse

    # HTTP response'u CSV için ayarla
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="sikayetler_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    )

    # CSV writer oluştur
    writer = csv.writer(response)

    # UTF-8 BOM ekle (Excel için)
    response.write("\ufeff")

    # Başlık satırı
    writer.writerow(
        [
            "Başlık",
            "Kategori",
            "Durum",
            "Öncelik",
            "Açıklama",
            "Şikayet Eden",
            "Oluşturma Tarihi",
            "Güncelleme Tarihi",
        ]
    )

    # Kullanıcının şikayetlerini al
    complaints = (
        Complaint.objects.filter(submitter=request.user)
        .select_related("category", "submitter")
        .order_by("-created_at")
    )

    # Şikayetleri CSV'ye yaz
    for complaint in complaints:
        writer.writerow(
            [
                complaint.title,
                complaint.category.name if complaint.category else "Kategori Yok",
                complaint.get_status_display(),
                (
                    complaint.get_priority_display()
                    if hasattr(complaint, "get_priority_display")
                    else "Normal"
                ),
                complaint.description,
                complaint.submitter.get_full_name() or complaint.submitter.username,
                complaint.created_at.strftime("%d.%m.%Y %H:%M"),
                complaint.updated_at.strftime("%d.%m.%Y %H:%M"),
            ]
        )

    return response


@login_required
def export_complaints_pdf(request):
    """
    Şikayetleri PDF formatında export eder (HTML print kullanarak)
    """
    from django.http import HttpResponse
    from django.template.loader import render_to_string

    # Kullanıcının şikayetlerini al
    complaints = (
        Complaint.objects.filter(submitter=request.user)
        .select_related("category", "submitter")
        .order_by("-created_at")
    )

    # Template render et
    html_string = render_to_string(
        "complaints/export_pdf.html",
        {
            "complaints": complaints,
            "user": request.user,
            "export_date": timezone.now(),
        },
    )

    # HTML response (print için)
    response = HttpResponse(html_string, content_type="text/html")

    return response
