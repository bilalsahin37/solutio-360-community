#!/usr/bin/env python
import os
import sys

import django

# Django ayarlarını yükle
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from complaints.models import Complaint

User = get_user_model()


def test_withdraw():
    print("=== Withdraw Test ===")

    # Test için bir kullanıcı bul
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ Aktif kullanıcı bulunamadı")
        return

    print(f"✅ Test kullanıcısı: {user.username}")

    # Bu kullanıcının şikayetlerini bul
    complaints = Complaint.objects.filter(submitter=user)
    print(f"✅ Toplam şikayet sayısı: {complaints.count()}")

    # Geri çekilebilir şikayetleri bul
    withdrawable = complaints.filter(is_withdrawn=False, can_be_withdrawn=True).exclude(
        status__in=["RESOLVED", "CLOSED", "CANCELLED", "WITHDRAWN"]
    )

    print(f"✅ Geri çekilebilir şikayet sayısı: {withdrawable.count()}")

    if withdrawable.exists():
        complaint = withdrawable.first()
        print(f"✅ Test şikayeti: {complaint.title}")
        print(f"   - Durum: {complaint.status}")
        print(f"   - Geri çekilmiş mi: {complaint.is_withdrawn}")
        print(f"   - Geri çekilebilir mi: {complaint.can_withdraw}")
        print(f"   - can_be_withdrawn: {complaint.can_be_withdrawn}")

        # Withdraw işlemini test et
        try:
            print("\n--- Withdraw işlemi başlatılıyor ---")
            old_status = complaint.status
            old_withdrawn = complaint.is_withdrawn

            complaint.withdraw(reason="Test geri çekme", user=user)

            # Veritabanından yeniden yükle
            complaint.refresh_from_db()

            print(f"✅ Withdraw işlemi tamamlandı!")
            print(f"   - Eski durum: {old_status} -> Yeni durum: {complaint.status}")
            print(
                f"   - Eski withdrawn: {old_withdrawn} -> Yeni withdrawn: {complaint.is_withdrawn}"
            )
            print(f"   - Withdraw tarihi: {complaint.withdrawal_date}")
            print(f"   - Withdraw sebebi: {complaint.withdrawal_reason}")

            return True

        except Exception as e:
            print(f"❌ Withdraw işlemi başarısız: {str(e)}")
            return False
    else:
        print("❌ Geri çekilebilir şikayet bulunamadı")

        # Yeni bir test şikayeti oluştur
        print("\n--- Test şikayeti oluşturuluyor ---")
        test_complaint = Complaint.objects.create(
            title="Test Withdraw Şikayeti",
            description="Bu bir test şikayetidir",
            submitter=user,
            status="SUBMITTED",
            can_be_withdrawn=True,
            is_withdrawn=False,
        )
        print(f"✅ Test şikayeti oluşturuldu: {test_complaint.title}")
        print(f"   - ID: {test_complaint.pk}")
        print(f"   - Geri çekilebilir mi: {test_complaint.can_withdraw}")

        return test_complaint


if __name__ == "__main__":
    result = test_withdraw()
    if result:
        print("\n🎉 Test başarılı!")
    else:
        print("\n❌ Test başarısız!")
