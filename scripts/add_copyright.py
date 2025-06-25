#!/usr/bin/env python3
"""
Telif Hakkı Header Ekleme Script'i
Tüm Python ve JavaScript dosyalarına copyright header ekler
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Telif hakkı header template'i
COPYRIGHT_HEADER_PYTHON = '''"""
Solutio 360 - Şikayet Yönetim Sistemi
Copyright (c) 2024 {owner}. Tüm hakları saklıdır.

Bu yazılım mülkiyet yazılımıdır ve telif hakkı yasaları ile korunmaktadır.
İzinsiz kopyalama, dağıtım veya değiştirme yasaktır.

Lisans: Proprietary
Website: {website}
Email: {email}
"""
'''

COPYRIGHT_HEADER_JS = """/**
 * Solutio 360 - Şikayet Yönetim Sistemi
 * Copyright (c) 2024 {owner}. Tüm hakları saklıdır.
 * 
 * Bu yazılım mülkiyet yazılımıdır ve telif hakkı yasaları ile korunmaktadır.
 * İzinsiz kopyalama, dağıtım veya değiştirme yasaktır.
 * 
 * Lisans: Proprietary
 * Website: {website}
 * Email: {email}
 */
"""

COPYRIGHT_HEADER_HTML = """<!--
Solutio 360 - Şikayet Yönetim Sistemi
Copyright (c) 2024 {owner}. Tüm hakları saklıdır.

Bu yazılım mülkiyet yazılımıdır ve telif hakkı yasaları ile korunmaktadır.
İzinsiz kopyalama, dağıtım veya değiştirme yasaktır.

Lisans: Proprietary
Website: {website}
Email: {email}
-->
"""

# Konfigürasyon
CONFIG = {
    "owner": "[İsminiz/Şirket Adınız]",
    "website": "https://solutio360.com",
    "email": "legal@solutio360.com",
}

# İşlenecek dosya türleri
FILE_PATTERNS = {
    ".py": COPYRIGHT_HEADER_PYTHON,
    ".js": COPYRIGHT_HEADER_JS,
    ".html": COPYRIGHT_HEADER_HTML,
    ".css": COPYRIGHT_HEADER_JS,  # CSS için JS style comment kullan
}

# Hariç tutulacak dizinler
EXCLUDE_DIRS = {
    "venv",
    "node_modules",
    ".git",
    "__pycache__",
    "migrations",
    "staticfiles",
    "media",
    ".vscode",
    "dist",
    "build",
    "coverage",
    ".pytest_cache",
}

# Hariç tutulacak dosyalar
EXCLUDE_FILES = {
    "manage.py",
    "__init__.py",
    "wsgi.py",
    "asgi.py",
    "settings.py",
    "urls.py",  # Django core dosyaları
}


def has_copyright_header(file_path):
    """Dosyada zaten copyright header var mı kontrol et"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_lines = f.read(500)  # İlk 500 karakter
            return "Copyright (c) 2024" in first_lines or "Solutio 360" in first_lines
    except:
        return False


def add_copyright_header(file_path, header_template):
    """Dosyaya copyright header ekle"""
    try:
        # Mevcut içeriği oku
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Header'ı konfigürasyonla doldur
        header = header_template.format(**CONFIG)

        # Shebang varsa onu koru
        if content.startswith("#!"):
            lines = content.split("\n")
            shebang = lines[0]
            rest_content = "\n".join(lines[1:])
            new_content = f"{shebang}\n{header}\n{rest_content}"
        else:
            new_content = f"{header}\n{content}"

        # Dosyayı güncelle
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"❌ Hata: {file_path} - {e}")
        return False


def process_directory(directory):
    """Dizini recursive olarak işle"""
    processed_files = 0
    skipped_files = 0
    error_files = 0

    for root, dirs, files in os.walk(directory):
        # Hariç tutulan dizinleri atla
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = Path(root) / file
            file_extension = file_path.suffix.lower()

            # Sadece belirli dosya türlerini işle
            if file_extension not in FILE_PATTERNS:
                continue

            # Hariç tutulan dosyaları atla
            if file in EXCLUDE_FILES:
                continue

            # Zaten copyright header varsa atla
            if has_copyright_header(file_path):
                print(f"⏭️  Atlanıyor (zaten var): {file_path}")
                skipped_files += 1
                continue

            # Copyright header ekle
            header_template = FILE_PATTERNS[file_extension]
            if add_copyright_header(file_path, header_template):
                print(f"✅ Eklendi: {file_path}")
                processed_files += 1
            else:
                print(f"❌ Hata: {file_path}")
                error_files += 1

    return processed_files, skipped_files, error_files


def main():
    """Ana fonksiyon"""
    print("🔒 Solutio 360 - Telif Hakkı Header Ekleme Tool'u")
    print("=" * 50)

    # Konfigürasyonu göster
    print(f"👤 Sahip: {CONFIG['owner']}")
    print(f"🌐 Website: {CONFIG['website']}")
    print(f"📧 Email: {CONFIG['email']}")
    print()

    # Onay al
    response = input("Devam etmek istiyor musunuz? (y/n): ")
    if response.lower() != "y":
        print("❌ İşlem iptal edildi.")
        return

    # Mevcut dizini işle
    current_dir = Path.cwd()
    print(f"📁 İşlenen dizin: {current_dir}")
    print()

    try:
        processed, skipped, errors = process_directory(current_dir)

        print("\n" + "=" * 50)
        print("📊 İŞLEM RAPORU")
        print("=" * 50)
        print(f"✅ İşlenen dosyalar: {processed}")
        print(f"⏭️  Atlanan dosyalar: {skipped}")
        print(f"❌ Hatalı dosyalar: {errors}")
        print(f"📈 Toplam kontrol: {processed + skipped + errors}")

        if errors == 0:
            print("\n🎉 Tüm dosyalar başarıyla işlendi!")
        else:
            print(f"\n⚠️  {errors} dosyada hata oluştu. Lütfen kontrol edin.")

    except KeyboardInterrupt:
        print("\n❌ İşlem kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\n❌ Genel hata: {e}")


if __name__ == "__main__":
    main()
