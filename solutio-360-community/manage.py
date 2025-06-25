#!/usr/bin/env python
"""
Django Yönetim Komut Satırı Aracı
=================================

Django'nun yönetimsel görevler için komut satırı aracı.
Veritabanı migrations, sunucu başlatma, test çalıştırma gibi
Django yönetim komutlarını çalıştırmak için kullanılır.

Kullanım örnekleri:
- python manage.py runserver (geliştirme sunucusu başlat)
- python manage.py migrate (veritabanı migrations uygula)
- python manage.py createsuperuser (admin kullanıcı oluştur)
- python manage.py collectstatic (statik dosyaları topla)
- python manage.py test (testleri çalıştır)

@author Django Software Foundation & Solutio 360 Team
"""
import os
import sys


def main():
    """
    Yönetimsel görevleri çalıştırır.

    Django'nun DJANGO_SETTINGS_MODULE environment variable'ını ayarlar
    ve komut satırından gelen argümanları Django'nun yönetim sistemine iletir.

    Raises:
        ImportError: Django yüklü değilse veya PYTHONPATH'te bulunamazsa
    """
    # Django ayarlar modülünü belirle
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")

    try:
        # Django'nun komut satırı yönetim sistemini import et
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Django import edilemezse hata mesajı göster
        raise ImportError(
            "Django import edilemedi. Django'nun yüklü olduğundan ve "
            "PYTHONPATH environment variable'ında mevcut olduğundan emin olun. "
            "Sanal ortamı (virtual environment) aktifleştirmeyi unuttunuz mu?"
        ) from exc

    # Komut satırı argümanlarını Django yönetim sistemine ilet
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    # Script doğrudan çalıştırıldığında main fonksiyonunu çağır
    main()
