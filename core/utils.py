"""
Core Uygulama Yardımcı Fonksiyonları - Solutio 360 PWA
======================================================

Bu modül core uygulaması için yardımcı fonksiyonları içerir.
Sistem genelinde kullanılan ortak işlevleri barındırır.

Ana Kategoriler:
- Dosya İşlemleri: Dosya adı, boyut, hash hesaplama
- Ağ İşlemleri: IP, User Agent bilgileri
- Bildirim Sistemi: Email ve uygulama bildirimleri
- Cache Yönetimi: Veri önbellekleme işlemleri
- SLA Hesaplamaları: Hizmet seviyesi anlaşması
- Zaman İşlemleri: Tarih/saat hesaplamaları
- Güvenlik: Dosya doğrulama, veri maskeleme
- Sistem Ayarları: Dinamik konfigürasyon
- Audit Log: Kullanıcı aktivite takibi
- Webhook: Harici sistem entegrasyonu

Güvenlik Özellikleri:
- Dosya adı sanitizasyonu
- Uzantı kontrolü
- Boyut kontrolü
- Hash doğrulama
- Veri maskeleme

Performans Özellikleri:
- Cache yönetimi
- Veritabanı optimizasyonu
- Bellek kullanım kontrolü
"""

import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from .constants import CACHE_KEYS, CACHE_TIMEOUTS


def generate_unique_filename(filename: str) -> str:
    """
    Benzersiz Dosya Adı Oluşturma
    ============================

    Yüklenen dosyalar için benzersiz dosya adı oluşturur.
    Çakışmaları önler ve güvenli dosya adları sağlar.

    İşlem Adımları:
    1. Dosya adını slug formatına çevir
    2. 8 karakterlik UUID ekle
    3. Orijinal uzantıyı koru
    4. Birleştirilmiş adı döndür

    Args:
        filename (str): Orijinal dosya adı

    Returns:
        str: Benzersiz dosya adı

    Example:
        >>> generate_unique_filename("my document.pdf")
        "my-document_a1b2c3d4.pdf"
    """
    name, ext = os.path.splitext(filename)
    unique_name = f"{slugify(name)}_{uuid.uuid4().hex[:8]}{ext}"
    return unique_name


def get_file_hash(file_content: bytes) -> str:
    """
    Dosya Hash Hesaplama
    ===================

    Dosya içeriğinin MD5 hash'ini hesaplar.
    Dosya bütünlüğü kontrolü ve tekrar yükleme tespiti için kullanılır.

    Kullanım Alanları:
    - Dosya bütünlük kontrolü
    - Tekrar yükleme tespiti
    - Deduplication (aynı dosya tespiti)
    - Güvenlik kontrolü

    Args:
        file_content (bytes): Dosya içeriği (byte formatında)

    Returns:
        str: MD5 hash değeri (hexadecimal)

    Example:
        >>> with open("file.txt", "rb") as f:
        ...     hash_value = get_file_hash(f.read())
        "5d41402abc4b2a76b9719d911017c592"
    """
    return hashlib.md5(file_content).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Dosya Boyutu Formatlama
    ======================

    Byte cinsinden dosya boyutunu okunabilir formata çevirir.
    Kullanıcı dostu görüntüleme için optimize edilmiştir.

    Desteklenen Birimler:
    - B (Byte)
    - KB (Kilobyte)
    - MB (Megabyte)
    - GB (Gigabyte)
    - TB (Terabyte)

    Args:
        size_bytes (int): Byte cinsinden dosya boyutu

    Returns:
        str: Formatlanmış boyut metni

    Example:
        >>> format_file_size(1024)
        "1.0 KB"
        >>> format_file_size(1048576)
        "1.0 MB"
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def get_client_ip(request) -> str:
    """
    İstemci IP Adresi Alma
    =====================

    HTTP isteğinden gerçek istemci IP adresini alır.
    Proxy ve load balancer durumlarını da dikkate alır.

    IP Alma Önceliği:
    1. HTTP_X_FORWARDED_FOR (proxy arkasındaki gerçek IP)
    2. REMOTE_ADDR (doğrudan bağlantı IP'si)

    Kullanım Alanları:
    - Güvenlik logları
    - Coğrafi konum tespiti
    - Rate limiting
    - Fraud detection

    Args:
        request: Django HTTP request nesnesi

    Returns:
        str: İstemci IP adresi

    Example:
        >>> get_client_ip(request)
        "192.168.1.100"
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(request) -> str:
    """
    Kullanıcı Tarayıcı Bilgisi Alma
    ==============================

    HTTP isteğinden User-Agent bilgisini alır.
    Tarayıcı, işletim sistemi ve cihaz tespiti için kullanılır.

    Kullanım Alanları:
    - Tarayıcı uyumluluk kontrolü
    - Mobil/desktop tespit
    - İstatistik toplama
    - Güvenlik analizi
    - Bot tespit

    Args:
        request: Django HTTP request nesnesi

    Returns:
        str: User-Agent string'i

    Example:
        >>> get_user_agent(request)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    """
    return request.META.get("HTTP_USER_AGENT", "")


def send_notification_email(user, subject: str, template: str, context: Dict[str, Any]) -> bool:
    """
    Bildirim Email Gönderme
    ======================

    Kullanıcılara HTML template tabanlı email bildirimi gönderir.
    Sistem bildirimleri, uyarılar ve bilgilendirmeler için kullanılır.

    Özellikler:
    - HTML template desteği
    - Context değişkenleri
    - Hata yönetimi
    - Güvenli gönderim

    Email Türleri:
    - Şikayet bildirimleri
    - Durum değişiklikleri
    - Sistem uyarıları
    - Hatırlatmalar

    Args:
        user: Alıcı kullanıcı nesnesi
        subject (str): Email konusu
        template (str): HTML template dosya yolu
        context (Dict[str, Any]): Template değişkenleri

    Returns:
        bool: Gönderim başarılı mı?

    Example:
        >>> context = {"user": user, "complaint_title": "Test"}
        >>> send_notification_email(
        ...     user,
        ...     "Yeni Şikayet",
        ...     "emails/complaint_notification.html",
        ...     context
        ... )
        True
    """
    try:
        html_message = render_to_string(template, context)
        send_mail(
            subject=subject,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email gönderme hatası: {e}")
        return False


def create_notification(user, message: str, notification_type: str = "INFO", url: str = "") -> None:
    """
    Uygulama İçi Bildirim Oluşturma
    ==============================

    Kullanıcı için uygulama içi bildirim oluşturur.
    Real-time bildirim sistemi ile entegre çalışır.

    Bildirim Türleri:
    - INFO: Bilgi bildirimi
    - SUCCESS: Başarı bildirimi
    - WARNING: Uyarı bildirimi
    - ERROR: Hata bildirimi

    Özellikler:
    - Bildirim türü kategorilendirmesi
    - URL yönlendirme desteği
    - Otomatik timestamp
    - Kullanıcı bazlı filtreleme

    Args:
        user: Bildirim alacak kullanıcı
        message (str): Bildirim mesajı
        notification_type (str): Bildirim türü (varsayılan: "INFO")
        url (str): Yönlendirme URL'i (isteğe bağlı)

    Returns:
        None

    Example:
        >>> create_notification(
        ...     user,
        ...     "Şikayetiniz başarıyla oluşturuldu",
        ...     "SUCCESS",
        ...     "/complaints/123/"
        ... )
    """
    from .models import Notification, NotificationType

    try:
        notification_type_obj, _ = NotificationType.objects.get_or_create(
            code=notification_type, defaults={"name": notification_type}
        )

        Notification.objects.create(user=user, message=message, type=notification_type_obj, url=url)
    except Exception as e:
        print(f"Bildirim oluşturma hatası: {e}")


def get_cached_data(cache_key: str, default: Any = None) -> Any:
    """
    Cache'den Veri Alma
    ==================

    Redis/Memcached cache'inden veri alır.
    Performans optimizasyonu için kullanılır.

    Cache Stratejisi:
    - Hit: Cache'de veri var, hızlı döndür
    - Miss: Cache'de veri yok, default döndür

    Kullanım Alanları:
    - Dashboard istatistikleri
    - Sık kullanılan veriler
    - API response'ları
    - Hesaplama sonuçları

    Args:
        cache_key (str): Cache anahtarı
        default (Any): Cache miss durumunda döndürülecek değer

    Returns:
        Any: Cache'deki veri veya default değer

    Example:
        >>> stats = get_cached_data("dashboard_stats_123", {})
        {"total_complaints": 45, "pending": 12}
    """
    return cache.get(cache_key, default)


def set_cached_data(cache_key: str, data: Any, timeout: int = CACHE_TIMEOUTS["MEDIUM"]) -> None:
    """
    Cache'e Veri Kaydetme
    ====================

    Redis/Memcached cache'ine veri kaydeder.
    TTL (Time To Live) ile otomatik temizleme.

    Cache Timeout Seviyeleri:
    - SHORT: 5 dakika (sık değişen veriler)
    - MEDIUM: 30 dakika (orta sıklık)
    - LONG: 2 saat (az değişen veriler)

    Kullanım Alanları:
    - Hesaplanmış istatistikler
    - API response'ları
    - Sık erişilen veriler
    - Session verileri

    Args:
        cache_key (str): Cache anahtarı
        data (Any): Kaydedilecek veri
        timeout (int): Cache süresi (saniye)

    Returns:
        None

    Example:
        >>> set_cached_data("user_stats_123", {"score": 95}, 1800)
    """
    cache.set(cache_key, data, timeout)


def invalidate_user_cache(user_id: int) -> None:
    """
    Kullanıcı Cache Temizleme
    ========================

    Belirli kullanıcıya ait tüm cache verilerini temizler.
    Veri güncellendiğinde cache tutarlılığını sağlar.

    Temizlenen Cache'ler:
    - Dashboard istatistikleri
    - Kullanıcı bildirimleri
    - Kişisel veriler
    - Yetki bilgileri

    Kullanım Senaryoları:
    - Kullanıcı profil güncelleme
    - Yetki değişiklikleri
    - Veri tutarlılığı sağlama
    - Manual cache temizleme

    Args:
        user_id (int): Kullanıcı ID'si

    Returns:
        None

    Example:
        >>> invalidate_user_cache(123)  # 123 ID'li kullanıcının cache'ini temizle
    """
    dashboard_key = CACHE_KEYS["DASHBOARD_STATS"].format(user_id=user_id)
    notifications_key = CACHE_KEYS["USER_NOTIFICATIONS"].format(user_id=user_id)

    cache.delete_many([dashboard_key, notifications_key])


def calculate_sla_due_date(created_at: datetime, sla_hours: int = 24) -> datetime:
    """
    SLA Bitiş Tarihi Hesaplama
    ==========================

    Hizmet Seviyesi Anlaşması (SLA) bitiş tarihini hesaplar.
    Şikayet çözüm süreleri ve deadline takibi için kullanılır.

    SLA Seviyeleri:
    - Kritik: 4 saat
    - Yüksek: 8 saat
    - Normal: 24 saat (varsayılan)
    - Düşük: 72 saat

    Kullanım Alanları:
    - Şikayet çözüm süreleri
    - Deadline uyarıları
    - Performans metrikleri
    - Raporlama

    Args:
        created_at (datetime): Başlangıç tarihi
        sla_hours (int): SLA süresi (saat, varsayılan: 24)

    Returns:
        datetime: SLA bitiş tarihi

    Example:
        >>> from datetime import datetime
        >>> created = datetime.now()
        >>> due_date = calculate_sla_due_date(created, 8)
        datetime(2024, 1, 15, 16, 30, 0)  # 8 saat sonra
    """
    return created_at + timedelta(hours=sla_hours)


def is_sla_breached(created_at: datetime, sla_hours: int = 24) -> bool:
    """
    SLA İhlali Kontrolü
    ==================

    SLA süresinin aşılıp aşılmadığını kontrol eder.
    Geciken işlemler için uyarı ve escalation tetikler.

    İhlal Durumları:
    - True: SLA süresi aşıldı (gecikme var)
    - False: SLA süresi içinde (zamanında)

    Kullanım Alanları:
    - Gecikme uyarıları
    - Escalation tetikleme
    - Performans raporları
    - Dashboard göstergeleri

    Args:
        created_at (datetime): Başlangıç tarihi
        sla_hours (int): SLA süresi (saat, varsayılan: 24)

    Returns:
        bool: SLA ihlali var mı?

    Example:
        >>> from datetime import datetime, timedelta
        >>> old_date = datetime.now() - timedelta(hours=30)
        >>> is_sla_breached(old_date, 24)
        True  # 30 saat geçmiş, 24 saatlik SLA aşılmış
    """
    due_date = calculate_sla_due_date(created_at, sla_hours)
    return timezone.now() > due_date


def get_time_diff_display(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """
    Zaman Farkı Görüntüleme
    ======================

    İki tarih arasındaki farkı kullanıcı dostu formatta gösterir.
    Sosyal medya tarzı "relatif zaman" gösterimi.

    Görüntü Formatları:
    - "Az önce" (1 dakikadan az)
    - "X dakika" (1-59 dakika)
    - "X saat" (1-23 saat)
    - "X gün" (1+ gün)

    Kullanım Alanları:
    - Şikayet oluşturma zamanı
    - Son aktivite gösterimi
    - Yorum zamanları
    - Feed timeline'ları

    Args:
        start_time (datetime): Başlangıç zamanı
        end_time (Optional[datetime]): Bitiş zamanı (varsayılan: şimdi)

    Returns:
        str: Formatlanmış zaman farkı

    Example:
        >>> from datetime import datetime, timedelta
        >>> past_time = datetime.now() - timedelta(hours=2)
        >>> get_time_diff_display(past_time)
        "2 saat"
    """
    if end_time is None:
        end_time = timezone.now()

    diff = end_time - start_time

    if diff.days > 0:
        return f"{diff.days} gün"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} saat"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} dakika"
    else:
        return "Az önce"


def sanitize_filename(filename: str) -> str:
    """
    Dosya adını güvenli hale getir
    """
    # Tehlikeli karakterleri kaldır
    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        filename = filename.replace(char, "_")

    # Dosya adını kısalt
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]

    return f"{name}{ext}"


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Dosya uzantısını kontrol et
    """
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip(".") in [ext.lower() for ext in allowed_extensions]


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Dosya boyutunu kontrol et
    """
    return file_size <= max_size


def generate_reference_number(prefix: str = "REF") -> str:
    """
    Referans numarası oluştur
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"


def mask_email(email: str) -> str:
    """
    Email adresini maskele
    """
    if "@" not in email:
        return email

    username, domain = email.split("@")

    if len(username) <= 2:
        masked_username = username
    else:
        masked_username = username[0] + "*" * (len(username) - 2) + username[-1]

    return f"{masked_username}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Telefon numarasını maskele
    """
    if len(phone) <= 4:
        return phone

    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


def get_system_setting(key: str, default: Any = None) -> Any:
    """
    Sistem ayarını al
    """
    from .models import SystemSettings

    return SystemSettings.get_setting(key, default)


def set_system_setting(
    key: str, value: Any, description: str = "", is_public: bool = False
) -> None:
    """
    Sistem ayarını kaydet
    """
    from .models import SystemSettings

    SystemSettings.set_setting(key, value, description, is_public)


def log_user_activity(
    user, action: str, object_id: str, changes: Dict[str, Any], request=None
) -> None:
    """
    Kullanıcı aktivitesini logla
    """
    from .models import AuditLog

    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name="Unknown",
            object_id=object_id,
            changes=changes,
            ip_address=get_client_ip(request) if request else None,
            user_agent=get_user_agent(request) if request else None,
        )
    except Exception as e:
        print(f"Audit log hatası: {e}")


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Metni belirtilen uzunlukta kes
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def get_model_verbose_name(model) -> str:
    """
    Model verbose name al
    """
    return model._meta.verbose_name if hasattr(model, "_meta") else str(model)


def create_webhook_payload(event_type: str, object_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Webhook payload oluştur
    """
    return {
        "event_type": event_type,
        "timestamp": timezone.now().isoformat(),
        "data": object_data,
        "version": "1.0",
    }
