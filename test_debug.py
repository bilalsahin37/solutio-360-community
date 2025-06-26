#!/usr/bin/env python
import os

import django

# Django ayarlarını yükle
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
django.setup()

from django.test import Client
from django.urls import reverse

from complaints.models import Complaint
from users.models import User


def debug_withdraw_issue():
    """Geri çekme sorunu debug et"""

    print("🔍 Geri çekme sorunu debug ediliyor...\n")

    # Test kullanıcısı bul
    user = User.objects.filter(username="bilalsahin37").first()
    if not user:
        print("❌ Test kullanıcısı bulunamadı!")
        return

    print(f"✅ Test kullanıcısı: {user.username}")

    # Son şikayetleri kontrol et
    complaints = Complaint.objects.filter(submitter=user).order_by("-created_at")[:5]
    print(f"\n📋 Son 5 şikayet:")

    for i, c in enumerate(complaints, 1):
        print(f"{i}. ID: {str(c.id)[:8]}...")
        print(f"   Başlık: {c.title[:50]}")
        print(f"   Durum: {c.status}")
        print(f"   can_withdraw: {c.can_withdraw}")
        print(f"   is_withdrawn: {c.is_withdrawn}")
        print(f"   can_be_withdrawn: {c.can_be_withdrawn}")
        print()

    # Geri çekilebilir bir şikayet bul
    test_complaint = (
        complaints.filter(can_be_withdrawn=True, is_withdrawn=False)
        .exclude(status__in=["RESOLVED", "CLOSED", "CANCELLED", "WITHDRAWN"])
        .first()
    )

    if not test_complaint:
        print("⚠️ Geri çekilebilir şikayet bulunamadı. Yeni test şikayeti oluşturuluyor...")
        test_complaint = Complaint.objects.create(
            title="Debug Test Şikayeti",
            description="Bu şikayet geri çekme debug testi için oluşturuldu.",
            submitter=user,
            status="SUBMITTED",
            can_be_withdrawn=True,
        )
        print(f"✅ Test şikayeti oluşturuldu: {test_complaint.id}")

    print(f"\n🎯 Test şikayeti seçildi:")
    print(f"   ID: {test_complaint.id}")
    print(f"   Başlık: {test_complaint.title}")
    print(f"   Durum: {test_complaint.status}")
    print(f"   can_withdraw: {test_complaint.can_withdraw}")

    # URL'i test et
    withdraw_url = reverse("complaints:withdraw_complaint", kwargs={"pk": test_complaint.id})
    print(f"\n🔗 Geri çekme URL'i: {withdraw_url}")

    # Client ile POST isteği test et
    client = Client()
    client.force_login(user)

    print(f"\n🚀 POST isteği gönderiliyor...")
    response = client.post(withdraw_url, {"withdrawal_reason": "Debug test sebebi"})

    print(f"   Status Code: {response.status_code}")
    print(f"   Redirect URL: {response.get('Location', 'Yok')}")

    # Şikayeti yeniden yükle ve kontrol et
    test_complaint.refresh_from_db()
    print(f"\n📊 İşlem sonrası durum:")
    print(f"   Durum: {test_complaint.status}")
    print(f"   is_withdrawn: {test_complaint.is_withdrawn}")
    print(f"   withdrawal_reason: {test_complaint.withdrawal_reason}")
    print(f"   withdrawal_date: {test_complaint.withdrawal_date}")
    print(f"   can_withdraw: {test_complaint.can_withdraw}")

    if test_complaint.is_withdrawn:
        print("\n✅ Geri çekme işlemi BAŞARILI!")
    else:
        print("\n❌ Geri çekme işlemi BAŞARISIZ!")

        # Hata nedenlerini kontrol et
        print("\n🔍 Hata nedenleri kontrol ediliyor:")
        print(f"   can_be_withdrawn: {test_complaint.can_be_withdrawn}")
        print(f"   is_withdrawn: {test_complaint.is_withdrawn}")
        print(f"   status: {test_complaint.status}")

        if test_complaint.status in ["RESOLVED", "CLOSED", "CANCELLED"]:
            print("   ❌ Şikayet durumu geri çekmeye uygun değil")
        if not test_complaint.can_be_withdrawn:
            print("   ❌ can_be_withdrawn False")
        if test_complaint.is_withdrawn:
            print("   ❌ Şikayet zaten geri çekilmiş")

    return test_complaint


if __name__ == "__main__":
    debug_withdraw_issue()
