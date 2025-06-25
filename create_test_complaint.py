#!/usr/bin/env python
import os
import sys

import django

# Django ayarlarını yükle
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
django.setup()

from django.contrib.auth import get_user_model

from complaints.models import Complaint, ComplaintCategory

User = get_user_model()


def create_test_complaint():
    # İlk kullanıcıyı bul
    user = User.objects.first()
    if not user:
        print("❌ Kullanıcı bulunamadı")
        return

    print(f"✅ Kullanıcı: {user.username}")

    # Test şikayeti oluştur
    complaint = Complaint.objects.create(
        title="Test Geri Çekme Şikayeti",
        description="Bu şikayet geri çekme işlemini test etmek için oluşturulmuştur.",
        submitter=user,
        status="SUBMITTED",  # Gönderildi durumunda
        priority="MEDIUM",
        is_withdrawn=False,
        can_be_withdrawn=True,
    )

    print(f"✅ Test şikayeti oluşturuldu: {complaint.title}")
    print(f"   - ID: {complaint.pk}")
    print(f"   - Durum: {complaint.status}")
    print(f"   - Geri çekilebilir mi: {complaint.can_withdraw}")
    print(f"   - is_withdrawn: {complaint.is_withdrawn}")
    print(f"   - can_be_withdrawn: {complaint.can_be_withdrawn}")

    return complaint


if __name__ == "__main__":
    create_test_complaint()
