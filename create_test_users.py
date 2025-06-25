#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test kullanıcıları oluşturma scripti
Solutio 360 PWA için farklı rollerde test kullanıcıları oluşturur
"""

import os
import sys

import django

# Django ayarlarını yükle
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
    django.setup()

import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from complaints.models import Complaint, ComplaintCategory

User = get_user_model()


def create_test_users():
    """Test kullanıcılarını oluştur"""

    print("🚀 Test kullanıcıları oluşturuluyor...")

    # 1. Superuser (Admin)
    if not User.objects.filter(username="admin").exists():
        admin_user = User.objects.create_user(
            username="admin",
            email="admin@solutio360.com",
            password="Admin123456",
            first_name="Sistem",
            last_name="Yöneticisi",
            is_staff=True,
            is_superuser=True,
        )
        print(f"✅ Admin kullanıcısı oluşturuldu: {admin_user.username}")
    else:
        admin_user = User.objects.get(username="admin")
        print(f"ℹ️  Admin kullanıcısı zaten mevcut: {admin_user.username}")

    # 2. Staff/Personnel Users (Personel Paneli için)
    staff_users = [
        {
            "username": "reviewer1",
            "email": "reviewer1@solutio360.com",
            "first_name": "Ayşe",
            "last_name": "Kızılcık",
            "password": "Test123456",
        },
        {
            "username": "reviewer2",
            "email": "reviewer2@solutio360.com",
            "first_name": "Mehmet",
            "last_name": "Yeşilova",
            "password": "Test123456",
        },
        {
            "username": "staff1",
            "email": "staff1@solutio360.com",
            "first_name": "Fatma",
            "last_name": "Soylu",
            "password": "Test123456",
        },
    ]

    for staff_data in staff_users:
        if not User.objects.filter(username=staff_data["username"]).exists():
            staff_user = User.objects.create_user(
                username=staff_data["username"],
                email=staff_data["email"],
                password=staff_data["password"],
                first_name=staff_data["first_name"],
                last_name=staff_data["last_name"],
                is_staff=True,  # Personel paneline erişim için
                is_active=True,
            )
            print(
                f"✅ Personel kullanıcısı oluşturuldu: {staff_user.username} - {staff_user.get_full_name()}"
            )
        else:
            staff_user = User.objects.get(username=staff_data["username"])
            # is_staff özelliğini güncelle
            staff_user.is_staff = True
            staff_user.save()
            print(
                f"ℹ️  Personel kullanıcısı güncellendi: {staff_user.username} - {staff_user.get_full_name()}"
            )

    # 3. Normal Users (Vatandaşlar)
    normal_users = [
        {
            "username": "testuser",
            "email": "testuser@solutio360.com",
            "first_name": "Ali",
            "last_name": "Veli",
            "password": "Test123456",
        },
        {
            "username": "citizen1",
            "email": "citizen1@example.com",
            "first_name": "Zeynep",
            "last_name": "Demir",
            "password": "Test123456",
        },
        {
            "username": "citizen2",
            "email": "citizen2@example.com",
            "first_name": "Burak",
            "last_name": "Kaya",
            "password": "Test123456",
        },
    ]

    for user_data in normal_users:
        if not User.objects.filter(username=user_data["username"]).exists():
            normal_user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_staff=False,
                is_active=True,
            )
            print(
                f"✅ Normal kullanıcı oluşturuldu: {normal_user.username} - {normal_user.get_full_name()}"
            )
        else:
            normal_user = User.objects.get(username=user_data["username"])
            print(
                f"ℹ️  Normal kullanıcı zaten mevcut: {normal_user.username} - {normal_user.get_full_name()}"
            )


def create_test_data():
    """Test verileri oluştur"""

    print("\n📄 Test verileri oluşturuluyor...")

    # Test kategorileri oluştur
    categories = [
        {
            "name": "Belediye Hizmetleri",
            "description": "Belediye ile ilgili şikayetler",
        },
        {"name": "Ulaşım", "description": "Ulaşım sorunları"},
        {"name": "Çevre", "description": "Çevre kirliliği ve sorunları"},
        {"name": "Sağlık", "description": "Sağlık hizmetleri ile ilgili sorunlar"},
        {"name": "Eğitim", "description": "Eğitim kurumları ile ilgili sorunlar"},
    ]

    for cat_data in categories:
        category, created = ComplaintCategory.objects.get_or_create(
            name=cat_data["name"],
            defaults={"description": cat_data["description"], "is_active": True},
        )
        if created:
            print(f"✅ Kategori oluşturuldu: {category.name}")
        else:
            print(f"ℹ️  Kategori zaten mevcut: {category.name}")

    # Test şikayetleri oluştur
    test_users = User.objects.filter(is_staff=False)
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    categories = ComplaintCategory.objects.all()

    if test_users.exists() and categories.exists():
        test_complaints = [
            {
                "title": "Park alanındaki çöp sorunu",
                "description": "Mahallemizdeki parkta çöp kutuları yeterli değil ve çöpler dağılmış durumda. Bu durum hem görüntü kirliliği hem de sağlık sorunu yaratıyor.",
                "priority": "MEDIUM",
                "status": "SUBMITTED",
            },
            {
                "title": "Yol bozukluğu acil müdahale",
                "description": "Ana cadde üzerindeki çukurlar araçlara zarar veriyor. Özellikle yağmurlu havalarda su birikintisi oluşuyor.",
                "priority": "HIGH",
                "status": "IN_REVIEW",
            },
            {
                "title": "Gürültü kirliliği şikayeti",
                "description": "Gece geç saatlerde yapılan inşaat çalışmaları nedeniyle uyuyamıyoruz. Lütfen gerekli önlemleri alın.",
                "priority": "MEDIUM",
                "status": "IN_PROGRESS",
            },
            {
                "title": "Otopark yetersizliği",
                "description": "Hastane önündeki otopark alanı hasta yakınları için yetersiz. Alternatif çözüm önerilerinizi bekliyoruz.",
                "priority": "LOW",
                "status": "SUBMITTED",
            },
            {
                "title": "Su kesintisi problemi",
                "description": "Son 3 gündür mahallemizde düzenli olarak su kesintileri yaşanıyor. Acil çözüm gerekiyor.",
                "priority": "CRITICAL",
                "status": "IN_REVIEW",
            },
        ]

        created_count = 0
        for i, complaint_data in enumerate(test_complaints):
            if not Complaint.objects.filter(title=complaint_data["title"]).exists():
                user = test_users[i % test_users.count()]
                category = categories[i % categories.count()]
                assigned_to = (
                    staff_users[i % staff_users.count()]
                    if staff_users.exists() and i % 2 == 0
                    else None
                )

                complaint = Complaint.objects.create(
                    title=complaint_data["title"],
                    description=complaint_data["description"],
                    submitter=user,
                    category=category,
                    priority=complaint_data["priority"],
                    status=complaint_data["status"],
                    assigned_to=assigned_to,
                    is_anonymous=False,
                )
                created_count += 1
                print(f"✅ Şikayet oluşturuldu: {complaint.title[:50]}...")

        if created_count == 0:
            print("ℹ️  Test şikayetleri zaten mevcut")
        else:
            print(f"✅ {created_count} adet yeni şikayet oluşturuldu")


def print_login_info():
    """Giriş bilgilerini yazdır"""

    print("\n" + "=" * 60)
    print("🔐 TEST KULLANICI GİRİŞ BİLGİLERİ")
    print("=" * 60)

    print("\n👑 YÖNETİCİ PANELİ:")
    print("   • Kullanıcı: admin")
    print("   • Şifre: Admin123456")
    print("   • Erişim: /admin/ (Django Admin)")

    print("\n👨‍💼 PERSONEL PANELİ:")
    print("   • Kullanıcı: reviewer1 / Şifre: Test123456")
    print("   • Kullanıcı: reviewer2 / Şifre: Test123456")
    print("   • Kullanıcı: staff1 / Şifre: Test123456")
    print("   • Erişim: /complaints/reviewer-panel/")

    print("\n👤 VATANDAŞ PANELİ:")
    print("   • Kullanıcı: testuser / Şifre: Test123456")
    print("   • Kullanıcı: citizen1 / Şifre: Test123456")
    print("   • Kullanıcı: citizen2 / Şifre: Test123456")
    print("   • Erişim: /complaints/ (Ana sayfa)")

    print("\n🔗 URL'ler:")
    print("   • Ana Sayfa: http://127.0.0.1:8000/")
    print("   • Şikayetler: http://127.0.0.1:8000/complaints/")
    print("   • Personel Paneli: http://127.0.0.1:8000/complaints/reviewer-panel/")
    print("   • Admin Panel: http://127.0.0.1:8000/admin/")
    print("   • Giriş: http://127.0.0.1:8000/accounts/login/")

    print(
        "\n💡 Not: Personel paneline erişmek için 'is_staff=True' olan kullanıcılar giriş yapmalı."
    )
    print("=" * 60)


if __name__ == "__main__":
    try:
        create_test_users()
        create_test_data()
        print_login_info()
        print("\n🎉 Tüm test kullanıcıları ve verileri başarıyla oluşturuldu!")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        sys.exit(1)
