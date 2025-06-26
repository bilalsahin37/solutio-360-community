"""
Core app views
Ana uygulama görünümleri
"""

import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import View

from complaints.models import Complaint, ComplaintCategory
from reports.models import Report
from users.models import User


class HealthCheckView(View):
    """Sistem durumu kontrolü class-based view."""

    def get(self, request, *args, **kwargs):
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            return JsonResponse(
                {
                    "status": "healthy",
                    "timestamp": timezone.now().isoformat(),
                    "database": "connected",
                    "version": "1.0.0",
                }
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": timezone.now().isoformat(),
                },
                status=503,
            )


class SystemInfoView(View):
    """Sistem bilgileri view."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        import platform
        import sys

        import django

        return JsonResponse(
            {
                "python_version": sys.version,
                "django_version": django.get_version(),
                "platform": platform.platform(),
                "server_time": timezone.now().isoformat(),
            }
        )


def ping_view(request):
    """Ping endpoint."""
    return JsonResponse({"status": "pong", "timestamp": timezone.now().isoformat()})


def stats_view(request):
    """Sistem istatistikleri."""
    return JsonResponse(
        {
            "total_complaints": Complaint.objects.count(),
            "total_users": User.objects.count(),
            "total_reports": Report.objects.count(),
            "timestamp": timezone.now().isoformat(),
        }
    )


def dashboard_view(request):
    """Dashboard view wrapper."""
    return dashboard(request)


def offline_view(request):
    """Offline sayfa."""
    return render(request, "offline.html")


@csrf_exempt
def pwa_install_stats(request):
    """PWA yükleme istatistikleri."""
    if request.method == "POST":
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def home(request):
    """Ana sayfa görünümü."""
    context = {
        "page_title": "Solutio 360 - Şikayet Yönetim Sistemi",
        "total_complaints": Complaint.objects.filter(is_active=True).count(),
        "categories": ComplaintCategory.objects.filter(
            is_active=True, parent__isnull=True
        ).order_by("order")[:6],
    }

    return render(request, "base/home.html", context)


@login_required
def dashboard(request):
    """Ana dashboard sayfası."""
    user = request.user

    context = {
        "user": user,
        "page_title": "Dashboard",
    }

    if user.is_staff:
        context.update(_get_admin_dashboard_data(user))
    else:
        context.update(_get_user_dashboard_data(user))

    return render(request, "base/dashboard.html", context)


def _get_admin_dashboard_data(user):
    """Admin için dashboard verileri."""
    last_30_days = timezone.now() - timedelta(days=30)
    last_7_days = timezone.now() - timedelta(days=7)
    today = timezone.now().date()

    # Temel sayılar
    total_complaints = Complaint.objects.filter(is_active=True).count()
    new_complaints = Complaint.objects.filter(created_at__gte=last_30_days, is_active=True).count()

    pending_complaints = Complaint.objects.filter(
        status__in=["SUBMITTED", "IN_REVIEW"], is_active=True
    ).count()

    resolved_complaints = Complaint.objects.filter(status="RESOLVED", is_active=True).count()

    # Detaylı durum istatistikleri
    status_stats = {
        "DRAFT": Complaint.objects.filter(status="DRAFT", is_active=True).count(),
        "SUBMITTED": Complaint.objects.filter(status="SUBMITTED", is_active=True).count(),
        "IN_REVIEW": Complaint.objects.filter(status="IN_REVIEW", is_active=True).count(),
        "IN_PROGRESS": Complaint.objects.filter(status="IN_PROGRESS", is_active=True).count(),
        "RESOLVED": Complaint.objects.filter(status="RESOLVED", is_active=True).count(),
        "CLOSED": Complaint.objects.filter(status="CLOSED", is_active=True).count(),
        "CANCELLED": Complaint.objects.filter(status="CANCELLED", is_active=True).count(),
        "WITHDRAWN": Complaint.objects.filter(status="WITHDRAWN", is_active=True).count(),
    }

    # Kategori istatistikleri
    category_stats = (
        Complaint.objects.filter(is_active=True)
        .values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # Günlük trend
    daily_complaints = []
    for i in range(30):
        date = timezone.now() - timedelta(days=i)
        count = Complaint.objects.filter(created_at__date=date.date(), is_active=True).count()
        daily_complaints.append({"date": date.strftime("%d.%m"), "count": count})
    daily_complaints.reverse()

    # Son aktiviteler
    recent_activities = Complaint.objects.filter(is_active=True).order_by("-created_at")[:5]

    # Kullanıcı istatistikleri
    total_users = User.objects.filter(is_active=True).count()
    new_users_this_month = User.objects.filter(
        date_joined__gte=timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ).count()

    # Rapor istatistikleri
    total_reports = Report.objects.filter(is_active=True).count()
    recent_reports = Report.objects.filter(created_at__gte=last_30_days, is_active=True).count()

    # Bugünkü aktivite
    today_complaints = Complaint.objects.filter(created_at__date=today, is_active=True).count()

    # Bu hafta oluşturulan şikayetler
    this_week_complaints = Complaint.objects.filter(
        created_at__gte=last_7_days, is_active=True
    ).count()

    # En aktif kullanıcılar
    top_users = (
        Complaint.objects.filter(is_active=True)
        .values("submitter__username", "submitter__first_name", "submitter__last_name")
        .annotate(complaint_count=Count("id"))
        .order_by("-complaint_count")[:5]
    )

    # Çözüm oranı hesaplama
    total_processed = Complaint.objects.filter(
        status__in=["RESOLVED", "CLOSED", "CANCELLED"], is_active=True
    ).count()
    resolution_rate = (resolved_complaints / total_processed * 100) if total_processed > 0 else 0

    return {
        "total_complaints": total_complaints,
        "new_complaints": new_complaints,
        "pending_complaints": pending_complaints,
        "resolved_complaints": resolved_complaints,
        "status_stats": status_stats,
        "category_stats": category_stats,
        "daily_complaints": daily_complaints,
        "recent_activities": recent_activities,
        "total_users": total_users,
        "new_users_this_month": new_users_this_month,
        "total_reports": total_reports,
        "recent_reports": recent_reports,
        "today_complaints": today_complaints,
        "this_week_complaints": this_week_complaints,
        "top_users": top_users,
        "resolution_rate": round(resolution_rate, 1),
        "is_admin_view": True,
    }


def _get_user_dashboard_data(user):
    """Normal kullanıcı için dashboard verileri."""
    last_30_days = timezone.now() - timedelta(days=30)
    user_complaints = Complaint.objects.filter(submitter=user, is_active=True)

    # Temel sayılar
    total_complaints = user_complaints.count()
    pending_complaints = user_complaints.filter(status__in=["SUBMITTED", "IN_REVIEW"]).count()
    resolved_complaints = user_complaints.filter(status="RESOLVED").count()

    # Durum bazlı dağılım
    status_counts = {
        "DRAFT": user_complaints.filter(status="DRAFT").count(),
        "SUBMITTED": user_complaints.filter(status="SUBMITTED").count(),
        "IN_REVIEW": user_complaints.filter(status="IN_REVIEW").count(),
        "IN_PROGRESS": user_complaints.filter(status="IN_PROGRESS").count(),
        "RESOLVED": user_complaints.filter(status="RESOLVED").count(),
        "CLOSED": user_complaints.filter(status="CLOSED").count(),
        "CANCELLED": user_complaints.filter(status="CANCELLED").count(),
        "WITHDRAWN": user_complaints.filter(status="WITHDRAWN").count(),
    }

    # Son şikayetler
    recent_complaints = user_complaints.order_by("-created_at")[:5]

    # Bu ay oluşturulan şikayetler
    this_month_complaints = user_complaints.filter(
        created_at__gte=timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ).count()

    # Kategori dağılımı
    category_stats = (
        user_complaints.values("category__name").annotate(count=Count("id")).order_by("-count")[:5]
    )

    return {
        "total_complaints": total_complaints,
        "pending_complaints": pending_complaints,
        "resolved_complaints": resolved_complaints,
        "this_month_complaints": this_month_complaints,
        "status_counts": status_counts,
        "recent_complaints": recent_complaints,
        "category_stats": category_stats,
        "is_admin_view": False,
    }


@login_required
def get_notifications(request):
    """Kullanıcı bildirimlerini JSON olarak döndür."""
    from users.models import UserNotification

    notifications = UserNotification.objects.filter(user=request.user).order_by("-created_at")[:20]

    notifications_data = []
    for notification in notifications:
        notifications_data.append(
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at.isoformat(),
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "url": notification.data.get("url", "") if notification.data else "",
            }
        )

    unread_count = UserNotification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({"notifications": notifications_data, "unread_count": unread_count})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Bildirimi okundu olarak işaretle."""
    from users.models import UserNotification

    try:
        notification = UserNotification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({"success": True})
    except UserNotification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Bildirim bulunamadı"})


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Tüm bildirimleri okundu olarak işaretle."""
    from users.models import UserNotification

    UserNotification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return JsonResponse({"success": True})


@login_required
def search_global(request):
    """Global arama fonksiyonu."""
    query = request.GET.get("q", "").strip()

    if not query or len(query) < 2:
        return JsonResponse({"results": [], "message": "En az 2 karakter giriniz"})

    results = []

    # Şikayet arama
    complaints = Complaint.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query), is_active=True
    )[:5]

    for complaint in complaints:
        results.append(
            {
                "type": "complaint",
                "title": complaint.title,
                "url": complaint.get_absolute_url(),
                "description": (
                    complaint.description[:100] + "..."
                    if len(complaint.description) > 100
                    else complaint.description
                ),
            }
        )

    # Kullanıcı arama (sadece admin'ler için)
    if request.user.is_staff:
        users = User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )[:5]

        for user in users:
            results.append(
                {
                    "type": "user",
                    "title": user.get_full_name() or user.username,
                    "url": f"/users/{user.id}/",
                    "description": user.email,
                }
            )

    # Rapor arama
    reports = Report.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query), is_active=True
    )[:5]

    for report in reports:
        results.append(
            {
                "type": "report",
                "title": report.name,
                "url": report.get_absolute_url(),
                "description": (
                    report.description[:100] + "..."
                    if len(report.description) > 100
                    else report.description
                ),
            }
        )

    return JsonResponse({"results": results, "query": query, "total": len(results)})


def health_check(request):
    """Sistem durumu kontrolü endpoint'i."""
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse(
            {
                "status": "healthy",
                "timestamp": timezone.now().isoformat(),
                "database": "connected",
                "version": "1.0.0",
            }
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=503,
        )


@csrf_exempt
def simple_chat_api(request):
    """🤖 Basit Chat API - Hızlı yanıt sistemi"""
    import random
    import re

    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        # JSON data parsing
        data = json.loads(request.body.decode("utf-8"))
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse(
                {
                    "status": "error",
                    "response": "Mesajınızı göremedim. Lütfen tekrar deneyin.",
                    "message": "Boş mesaj",
                },
                status=400,
            )

        # Türkçe akıllı yanıt sistemi
        message_lower = message.lower()

        # Şikayet ve problem durumları
        if any(
            word in message_lower
            for word in [
                "şikayet",
                "problem",
                "sorun",
                "hata",
                "çekemiyorum",
                "yapamıyorum",
            ]
        ):
            responses = [
                f"'{message}' konusundaki sorununuzu anlıyorum. Size yardımcı olmak için buradayım. Daha detaylı anlatabilir misiniz?",
                f"Belirttiğiniz sorun '{message}' hakkında analiz yapıyorum. Bu konuda size çözüm önerileri sunabilirim.",
                f"Şikayetinizi '{message}' sistemimize kaydettim. Sorununuz öncelikli olarak değerlendirilecek.",
            ]
            sentiment = "olumsuz"
            category = "Şikayet"

        # Selamlama
        elif any(word in message_lower for word in ["merhaba", "selam", "hello", "hi", "hey"]):
            responses = [
                "Merhaba! Ben Solutio 360 AI asistanıyım. Size nasıl yardımcı olabilirim? 😊",
                "Selam! Şikayetlerinizi analiz edebilir, sorularınızı yanıtlayabilirim. Ne konuda yardıma ihtiyacınız var?",
                "Merhaba! Bugün size nasıl destek olabilirim? Şikayet yönetimi konusunda uzmanım.",
            ]
            sentiment = "olumlu"
            category = "Selamlama"

        # Teşekkür
        elif any(
            word in message_lower for word in ["teşekkür", "sağol", "merci", "thanks", "eyvallah"]
        ):
            responses = [
                "Rica ederim! Size yardımcı olabildiğim için mutluyum. Başka sorularınız varsa çekinmeyin. 😊",
                "Ne demek! Solutio 360 ekibi olarak her zaman hizmetinizdeyiz. İyi günler!",
                "Memnun olduğunuzu duymak harika! Başka bir konuda yardım isterseniz buradayım.",
            ]
            sentiment = "olumlu"
            category = "Teşekkür"

        # Yardım talepleri
        elif any(word in message_lower for word in ["yardım", "help", "destek", "nasıl"]):
            responses = [
                "Tabii ki size yardımcı olabilirim! Şikayet yönetimi, raporlama veya sistem kullanımı hakkında sorularınızı yanıtlayabilirim.",
                "Yardım için buradayım! Hangi konuda destek istiyorsunuz? Şikayet oluşturma, takip etme veya başka bir konu mu?",
                "Size nasıl yardımcı olabileceğimi söyleyin. Sistem hakkında bilgi verebilir, şikayetlerinizi analiz edebilirim.",
            ]
            sentiment = "nötr"
            category = "Yardım"

        # Fatura/ödeme
        elif any(word in message_lower for word in ["fatura", "ödeme", "ücret", "para", "borç"]):
            responses = [
                "Fatura ve ödeme konularında size yardımcı olabilirim. Hangi konuda sorun yaşıyorsunuz?",
                "Ödeme ile ilgili sorununuzu anlıyorum. Mali işler departmanına yönlendirmek için detayları alabilir miyim?",
                "Fatura sorunlarınızı çözmek için elimden geleni yapacağım. Daha fazla bilgi verir misiniz?",
            ]
            sentiment = "nötr"
            category = "Fatura"

        # Teknik destek
        elif any(
            word in message_lower
            for word in ["teknik", "sistem", "çalışmıyor", "açılmıyor", "hata"]
        ):
            responses = [
                "Teknik sorununuzu anlıyorum. Teknik destek ekibimiz size yardımcı olacak. Sorunu daha detaylı anlatabilir misiniz?",
                "Sistem ile ilgili yaşadığınız sorunu çözmek için buradayım. Hangi bölümde sorun yaşıyorsunuz?",
                "Teknik problemleri çözmek konusunda uzmanım. Sorununuzu adım adım çözmeye çalışalım.",
            ]
            sentiment = "nötr"
            category = "Teknik"

        # Genel durumlar
        else:
            responses = [
                f"'{message}' konusunda size yardımcı olmaya çalışacağım. Bu konu hakkında daha fazla bilgi verebilir misiniz?",
                f"Mesajınızı '{message}' aldım ve analiz ediyorum. Size nasıl en iyi şekilde yardımcı olabilirim?",
                f"'{message}' konusunu değerlendiriyorum. Bu durumla ilgili size uygun çözümler önerebilirim.",
            ]
            sentiment = "nötr"
            category = "Genel"

        # Rastgele yanıt seç
        ai_response = random.choice(responses)

        # İşlem süresini simüle et
        processing_time = round(random.uniform(0.3, 1.5), 2)

        # Analiz verisi
        analysis = {
            "sentiment": sentiment,
            "category": category,
            "confidence": round(random.uniform(0.80, 0.95), 2),
            "keywords": re.findall(r"\w+", message_lower)[:3],
            "processing_time": processing_time,
            "message_length": len(message),
            "language": "turkish",
            "response_type": "instant",
        }

        return JsonResponse(
            {
                "status": "success",
                "response": ai_response,
                "message": ai_response,  # Compatibility
                "analysis": analysis,
                "timestamp": timezone.now().isoformat(),
                "user_message": message,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "response": "Mesaj formatı hatalı. Lütfen tekrar deneyin.",
                "error": "JSON parse error",
            },
            status=400,
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "response": "Üzgünüm, şu anda teknik bir sorun yaşıyorum. Lütfen biraz sonra tekrar deneyin.",
                "error": str(e),
            },
            status=500,
        )


def test_chat_view(request):
    """Test chat sayfası"""
    return HttpResponse(
        """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Test</title>
    <meta name="csrf-token" content="{csrf_token}">
</head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h1>Chat Test Sayfası</h1>
    <p>Bu sayfa chat widget'ını test etmek için oluşturulmuştur.</p>
    
    <!-- Clean Chat Widget -->
    <div id="clean-chat" style="position: fixed; bottom: 20px; right: 20px; z-index: 10000;">
        <button id="chat-btn" style="
            width: 60px; height: 60px; border-radius: 50%; border: none;
            background: #007bff; color: white; font-size: 24px; cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        ">💬</button>
        
        <div id="chat-window" style="
            position: absolute; bottom: 70px; right: 0; width: 320px; height: 400px;
            background: white; border: 1px solid #ddd; border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15); display: none; flex-direction: column;
        ">
            <div style="background: #007bff; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                <strong>AI Asistan</strong>
                <button onclick="closeChat()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer;">&times;</button>
            </div>
            
            <div id="messages" style="flex: 1; padding: 15px; overflow-y: auto; background: #f8f9fa;">
                <div style="background: #e9ecef; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px;">
                    Merhaba! Size nasıl yardımcı olabilirim?
                </div>
            </div>
            
            <div style="padding: 15px; display: flex; gap: 10px; border-top: 1px solid #eee;">
                <input type="text" id="msg-input" placeholder="Mesajınızı yazın..." style="flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none;">
                <button onclick="sendMsg()" style="padding: 12px 18px; background: #007bff; color: white; border: none; border-radius: 25px; cursor: pointer;">Gönder</button>
            </div>
        </div>
    </div>

    <script>
    let chatOpen = false;
    
    function toggleChat() {{
        const chatWindow = document.getElementById('chat-window');
        chatOpen = !chatOpen;
        chatWindow.style.display = chatOpen ? 'flex' : 'none';
        if (chatOpen) {{
            setTimeout(() => document.getElementById('msg-input').focus(), 100);
        }}
    }}
    
    function closeChat() {{
        chatOpen = false;
        document.getElementById('chat-window').style.display = 'none';
    }}
    
    function addMsg(text, isUser = false) {{
        const messages = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            background: ${{isUser ? '#007bff' : '#e9ecef'}};
            color: ${{isUser ? 'white' : '#333'}};
            padding: 10px 15px; border-radius: 18px; margin-bottom: 10px;
            max-width: 85%; word-wrap: break-word;
            ${{isUser ? 'margin-left: auto; text-align: right;' : ''}}
        `;
        messageDiv.textContent = text;
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }}
    
    async function sendMsg() {{
        const input = document.getElementById('msg-input');
        const message = input.value.trim();
        if (!message) return;
        
        addMsg(message, true);
        input.value = '';
        addMsg('AI yazıyor...', false);
        
        try {{
            const response = await fetch('/api/chat/', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ message: message }})
            }});
            
            document.getElementById('messages').lastChild.remove();
            
            if (response.ok) {{
                const data = await response.json();
                addMsg(data.response || 'Yanıt alınamadı.');
            }} else {{
                addMsg('Bağlantı hatası.');
            }}
        }} catch (error) {{
            document.getElementById('messages').lastChild.remove();
            addMsg('Ağ hatası.');
            console.error('Chat error:', error);
        }}
    }}
    
    // Initialize
    document.getElementById('chat-btn').onclick = toggleChat;
    document.getElementById('msg-input').onkeypress = function(e) {{
        if (e.key === 'Enter') sendMsg();
    }};
    
    console.log('✅ Chat test page loaded successfully');
    </script>
</body>
</html>
    """.format(
            csrf_token=get_token(request)
        )
    )
