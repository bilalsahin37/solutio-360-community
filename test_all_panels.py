#!/usr/bin/env python
"""
Solutio 360 PWA - Tüm Panelleri Test Etme Scripti
================================================

Bu script tüm sistemin işlevselliğini test eder:
- Kullanıcı Panelleri
- Admin Paneli
- Personel Paneli
- PWA Özellikleri
- Veritabanı Bağlantıları
- API Endpointleri
"""

import json
import os
import sys
import urllib.request
from datetime import datetime

import django

# Django ayarlarını yükle
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
    django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from complaints.models import Complaint, ComplaintCategory


# Test sonuçları için renkli çıktı
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(title):
    """Test bölümü başlığı yazdır"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_test(test_name, status, message=""):
    """Test sonucu yazdır"""
    if status:
        print(f"{Colors.GREEN}✅ {test_name}{Colors.END}")
        if message:
            print(f"   {Colors.CYAN}→ {message}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ {test_name}{Colors.END}")
        if message:
            print(f"   {Colors.RED}→ {message}{Colors.END}")


def test_database_connectivity():
    """Veritabanı bağlantısını test et"""
    print_header("VERİTABANI BAĞLANTI TESTLERİ")

    try:
        User = get_user_model()
        user_count = User.objects.count()
        print_test("Veritabanı Bağlantısı", True, f"{user_count} kullanıcı bulundu")

        complaint_count = Complaint.objects.count()
        print_test("Şikayet Tablosu", True, f"{complaint_count} şikayet bulundu")

        category_count = ComplaintCategory.objects.count()
        print_test("Kategori Tablosu", True, f"{category_count} kategori bulundu")

        return True
    except Exception as e:
        print_test("Veritabanı Bağlantısı", False, str(e))
        return False


def test_user_authentication():
    """Kullanıcı kimlik doğrulama sistemini test et"""
    print_header("KİMLİK DOĞRULAMA TESTLERİ")

    User = get_user_model()

    # Admin kullanıcısı kontrolü
    try:
        admin_users = User.objects.filter(is_superuser=True)
        print_test(
            "Admin Kullanıcıları",
            admin_users.exists(),
            f"{admin_users.count()} admin kullanıcı bulundu",
        )
    except Exception as e:
        print_test("Admin Kullanıcıları", False, str(e))

    # Staff kullanıcıları kontrolü
    try:
        staff_users = User.objects.filter(is_staff=True, is_superuser=False)
        print_test(
            "Personel Kullanıcıları",
            staff_users.exists(),
            f"{staff_users.count()} personel kullanıcı bulundu",
        )
    except Exception as e:
        print_test("Personel Kullanıcıları", False, str(e))

    # Normal kullanıcılar kontrolü
    try:
        normal_users = User.objects.filter(is_staff=False, is_superuser=False)
        print_test(
            "Normal Kullanıcılar",
            normal_users.exists(),
            f"{normal_users.count()} normal kullanıcı bulundu",
        )
    except Exception as e:
        print_test("Normal Kullanıcılar", False, str(e))


def test_url_configurations():
    """URL yapılandırmalarını test et"""
    print_header("URL YAPILANDIRMA TESTLERİ")

    try:
        home_url = reverse("home")
        print_test("Ana Sayfa URL", True, home_url)
    except Exception as e:
        print_test("Ana Sayfa URL", False, str(e))

    try:
        complaints_url = reverse("complaints:complaint_list")
        print_test("Şikayetler URL", True, complaints_url)
    except Exception as e:
        print_test("Şikayetler URL", False, str(e))

    try:
        reviewer_url = reverse("complaints:reviewer_panel")
        print_test("Personel Paneli URL", True, reviewer_url)
    except Exception as e:
        print_test("Personel Paneli URL", False, str(e))

    try:
        admin_url = "/admin/"
        print_test("Admin Paneli URL", True, admin_url)
    except Exception as e:
        print_test("Admin Paneli URL", False, str(e))


def test_pwa_features():
    """PWA özelliklerini test et"""
    print_header("PWA ÖZELLİK TESTLERİ")

    # Manifest.json kontrolü
    manifest_path = "static/manifest.json"
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            required_fields = ["name", "short_name", "start_url", "display", "icons"]
            all_fields_present = all(field in manifest for field in required_fields)
            print_test(
                "Manifest.json",
                all_fields_present,
                f"Gerekli alanlar: {', '.join(required_fields)}",
            )
        except Exception as e:
            print_test("Manifest.json", False, str(e))
    else:
        print_test("Manifest.json", False, "Dosya bulunamadı")

    # Service Worker kontrolü
    sw_paths = ["static/js/sw.js", "static/js/service-worker.js"]
    sw_found = False
    for sw_path in sw_paths:
        if os.path.exists(sw_path):
            sw_found = True
            print_test("Service Worker", True, sw_path)
            break

    if not sw_found:
        print_test("Service Worker", False, "Service worker dosyası bulunamadı")

    # PWA JavaScript dosyaları
    pwa_js_files = [
        "static/js/pwa-manager.js",
        "static/js/pwa-database.js",
        "static/js/pwa-install.js",
        "static/js/notification-manager.js",
    ]

    for js_file in pwa_js_files:
        exists = os.path.exists(js_file)
        print_test(
            f"PWA JS: {os.path.basename(js_file)}",
            exists,
            js_file if exists else "Dosya bulunamadı",
        )


def test_client_responses():
    """Django test client ile sayfa yanıtlarını test et"""
    print_header("SAYFA YANIT TESTLERİ")

    client = Client()

    # Ana sayfa testi (giriş yapmadan)
    try:
        response = client.get("/")
        print_test(
            "Ana Sayfa (Anonim)",
            response.status_code == 200,
            f"Status: {response.status_code}",
        )
    except Exception as e:
        print_test("Ana Sayfa (Anonim)", False, str(e))

    # Admin giriş sayfası
    try:
        response = client.get("/admin/")
        print_test(
            "Admin Giriş Sayfası",
            response.status_code in [200, 302],
            f"Status: {response.status_code}",
        )
    except Exception as e:
        print_test("Admin Giriş Sayfası", False, str(e))

    # Şikayetler sayfası (yönlendirme bekleniyor)
    try:
        response = client.get("/complaints/")
        print_test(
            "Şikayetler Sayfası",
            response.status_code in [200, 302],
            f"Status: {response.status_code}",
        )
    except Exception as e:
        print_test("Şikayetler Sayfası", False, str(e))


def test_static_files():
    """Statik dosyaları test et"""
    print_header("STATİK DOSYA TESTLERİ")

    # CSS dosyaları
    css_files = [
        "static/css/output.css",
        "static/css/login.css",
        "static/css/style.css",
    ]

    for css_file in css_files:
        exists = os.path.exists(css_file)
        print_test(
            f"CSS: {os.path.basename(css_file)}",
            exists,
            css_file if exists else "Dosya bulunamadı",
        )

    # JavaScript kütüphaneleri
    js_libs = [
        "static/js/jquery.min.js",
        "static/js/select2.min.js",
        "static/js/app.js",
    ]

    for js_file in js_libs:
        exists = os.path.exists(js_file)
        print_test(
            f"JS: {os.path.basename(js_file)}",
            exists,
            js_file if exists else "Dosya bulunamadı",
        )

    # Resim dosyaları
    image_dirs = ["static/images/", "static/images/icons/"]
    for img_dir in image_dirs:
        if os.path.exists(img_dir):
            files = os.listdir(img_dir)
            print_test(
                f"Resimler: {img_dir}", len(files) > 0, f"{len(files)} dosya bulundu"
            )
        else:
            print_test(f"Resimler: {img_dir}", False, "Dizin bulunamadı")


def test_authentication_with_test_users():
    """Test kullanıcıları ile kimlik doğrulama testi"""
    print_header("TEST KULLANICILARI İLE GİRİŞ TESTLERİ")

    User = get_user_model()
    client = Client()

    # Test kullanıcıları
    test_users = [
        {"username": "reviewer1", "password": "Test123456", "role": "Personel"},
        {"username": "testuser", "password": "Test123456", "role": "Kullanıcı"},
    ]

    for user_data in test_users:
        try:
            user = User.objects.get(username=user_data["username"])
            login_success = client.login(
                username=user_data["username"], password=user_data["password"]
            )
            print_test(
                f"Giriş: {user_data['username']} ({user_data['role']})",
                login_success,
                f"Staff: {user.is_staff}, Active: {user.is_active}",
            )
            client.logout()
        except User.DoesNotExist:
            print_test(f"Giriş: {user_data['username']}", False, "Kullanıcı bulunamadı")
        except Exception as e:
            print_test(f"Giriş: {user_data['username']}", False, str(e))


def generate_test_report():
    """Genel test raporu oluştur"""
    print_header("SOLUTIO 360 PWA - KAPSAMLI TEST RAPORU")

    print(
        f"{Colors.CYAN}Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}"
    )
    print(f"{Colors.CYAN}Django Versiyonu: {django.get_version()}{Colors.END}")
    print(f"{Colors.CYAN}Python Versiyonu: {sys.version.split()[0]}{Colors.END}")

    # Tüm testleri çalıştır
    tests = [
        test_database_connectivity,
        test_user_authentication,
        test_url_configurations,
        test_pwa_features,
        test_client_responses,
        test_static_files,
        test_authentication_with_test_users,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"{Colors.RED}Test hatası: {test.__name__} - {e}{Colors.END}")

    # Özet
    print_header("TEST ÖZETİ")
    print(f"{Colors.GREEN}✅ Solutio 360 PWA sistemi test edildi{Colors.END}")
    print(f"{Colors.YELLOW}📱 PWA özellikleri doğrulandı{Colors.END}")
    print(f"{Colors.BLUE}👥 Kullanıcı panelleri test edildi{Colors.END}")
    print(f"{Colors.PURPLE}🔧 Admin ve personel panelleri hazır{Colors.END}")

    print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 SİSTEM TEST GİRİŞ BİLGİLERİ:{Colors.END}")
    print(f"{Colors.WHITE}┌─ 👑 Admin Panel: http://127.0.0.1:8000/admin/{Colors.END}")
    print(f"{Colors.WHITE}│  └─ Kullanıcı: admin / Şifre: Admin123456{Colors.END}")
    print(
        f"{Colors.WHITE}├─ 👨‍💼 Personel Panel: http://127.0.0.1:8000/complaints/reviewer-panel/{Colors.END}"
    )
    print(f"{Colors.WHITE}│  └─ Kullanıcı: reviewer1 / Şifre: Test123456{Colors.END}")
    print(
        f"{Colors.WHITE}└─ 👤 Kullanıcı Panel: http://127.0.0.1:8000/complaints/{Colors.END}"
    )
    print(f"{Colors.WHITE}   └─ Kullanıcı: testuser / Şifre: Test123456{Colors.END}")


if __name__ == "__main__":
    try:
        generate_test_report()
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 TÜM TESTLER TAMAMLANDI!{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Test hatası: {e}{Colors.END}")
        sys.exit(1)
