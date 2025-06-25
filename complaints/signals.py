# -*- coding: utf-8 -*-
"""
Complaints Signals
Şikayet işlemlerini dinleyen ve tepki veren sinyal fonksiyonları
Circular import problemini önlemek için basitleştirilmiş versiyon
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Complaint

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Complaint)
def complaint_post_save(sender, instance, created, **kwargs):
    """
    Şikayet kaydedildikten sonra ML işlemlerini tetikle
    """
    if created:
        logger.info(f"Yeni şikayet oluşturuldu: {instance.id}")

        # ML işlemlerini async task olarak başlat (import döngüsünü önlemek için)
        try:
            from analytics.tasks import process_new_complaint_ml

            process_new_complaint_ml.delay(instance.id)
        except ImportError:
            # Analytics app henüz hazır değilse logla ve devam et
            logger.warning(
                "Analytics tasks import edilemedi, ML işlemleri yapılamayacak"
            )
        except Exception as e:
            logger.error(f"ML task başlatma hatası: {e}")


@receiver(pre_save, sender=Complaint)
def complaint_status_tracking(sender, instance, **kwargs):
    """
    Şikayet durumu değişikliklerini takip et
    """
    if instance.pk:  # Mevcut bir kayıt güncelleniyorsa
        try:
            old_instance = Complaint.objects.get(pk=instance.pk)

            # Durum değişikliği kontrolü
            if old_instance.status != instance.status:
                logger.info(
                    f"Şikayet {instance.id} durumu değişti: {old_instance.status} -> {instance.status}"
                )
                instance._status_changed = True
                instance._old_status = old_instance.status
                instance._new_status = instance.status

            # Açıklama değişikliği kontrolü
            if old_instance.description != instance.description:
                instance._description_changed = True

        except Complaint.DoesNotExist:
            # Yeni kayıt
            instance._status_changed = False
            instance._description_changed = True


@receiver(post_save, sender=Complaint)
def complaint_status_changed(sender, instance, created, **kwargs):
    """
    Şikayet durumu değiştiğinde ML modellerini güncelle
    """
    if (
        not created
        and hasattr(instance, "_status_changed")
        and instance._status_changed
    ):
        try:
            # ML feedback'i async task olarak başlat
            from analytics.tasks import process_complaint_status_change_ml

            process_complaint_status_change_ml.delay(
                instance.id, instance._old_status, instance._new_status
            )
        except ImportError:
            logger.warning(
                "Analytics tasks import edilemedi, ML feedback yapılamayacak"
            )
        except Exception as e:
            logger.error(f"ML status change task başlatma hatası: {e}")


@receiver(post_save, sender=Complaint)
def complaint_description_changed(sender, instance, created, **kwargs):
    """
    Şikayet açıklaması değiştiğinde yeniden analiz et
    """
    if (
        not created
        and hasattr(instance, "_description_changed")
        and instance._description_changed
    ):
        try:
            # NLP analizi async task olarak başlat
            from analytics.tasks import reanalyze_complaint_content

            reanalyze_complaint_content.delay(instance.id)
        except ImportError:
            logger.warning(
                "Analytics tasks import edilemedi, NLP analizi yapılamayacak"
            )
        except Exception as e:
            logger.error(f"NLP reanalysis task başlatma hatası: {e}")


def calculate_simple_priority(complaint):
    """
    Basit öncelik hesaplama
    """
    score = 0

    description = complaint.description or ""

    # Anahtar kelimeler
    urgent_keywords = ["acil", "urgent", "kritik", "critical", "asap", "hemen"]
    high_keywords = ["önemli", "important", "problem", "sorun", "issue"]

    description_lower = description.lower()

    for keyword in urgent_keywords:
        if keyword in description_lower:
            score += 3

    for keyword in high_keywords:
        if keyword in description_lower:
            score += 1

    # Uzunluk faktörü
    if len(description) > 500:
        score += 1

    # Saat faktörü (iş saatleri dışı)
    if complaint.created_at.hour < 8 or complaint.created_at.hour > 18:
        score += 1

    return score


def suggest_priority_from_content(complaint):
    """
    İçeriğe göre öncelik önerisi
    """
    score = calculate_simple_priority(complaint)

    if score >= 5:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"


def extract_keywords_from_complaint(complaint):
    """
    Şikayetten anahtar kelimeleri çıkar
    """
    if not complaint.description:
        return []

    # Basit keyword extraction
    text = complaint.description.lower()

    # Yaygın şikayet kategorileri
    category_keywords = {
        "technical": ["teknik", "technical", "bug", "hata", "çalışmıyor", "broken"],
        "billing": ["fatura", "billing", "payment", "ödeme", "ücret", "para"],
        "service": ["servis", "service", "destek", "support", "yardım", "help"],
        "quality": ["kalite", "quality", "kötü", "bad", "iyi değil", "poor"],
        "delivery": ["teslimat", "delivery", "kargo", "shipping", "geç", "late"],
    }

    found_keywords = []
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text:
                found_keywords.append((category, keyword))

    return found_keywords


def estimate_resolution_time(complaint):
    """
    Basit çözüm süresi tahmini (saat cinsinden)
    """
    base_time = 24  # 24 saat default

    # Öncelik faktörü
    if complaint.priority == "high":
        base_time = 4
    elif complaint.priority == "medium":
        base_time = 12
    elif complaint.priority == "low":
        base_time = 48

    # Kategori faktörü
    if complaint.category:
        category_name = complaint.category.name.lower()
        if "teknik" in category_name or "technical" in category_name:
            base_time *= 1.5  # Teknik sorunlar daha uzun sürer
        elif "fatura" in category_name or "billing" in category_name:
            base_time *= 0.5  # Fatura sorunları daha hızlı çözülür

    # Açıklama uzunluğu faktörü
    if complaint.description:
        desc_len = len(complaint.description)
        if desc_len > 1000:
            base_time *= 1.3  # Uzun açıklamalar daha karmaşık
        elif desc_len < 100:
            base_time *= 0.8  # Kısa açıklamalar daha basit

    return round(base_time, 1)
