import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Test kullanıcıları oluştur
users_data = [
    {
        "username": "reviewer1",
        "email": "reviewer1@solutio360.com",
        "first_name": "Ahmet",
        "last_name": "Yılmaz",
        "password": "Test123456",
        "is_staff": True,
    },
    {
        "username": "reviewer2",
        "email": "reviewer2@solutio360.com",
        "first_name": "Zeynep",
        "last_name": "Kaya",
        "password": "Test123456",
        "is_staff": True,
    },
    {
        "username": "testuser",
        "email": "testuser@solutio360.com",
        "first_name": "Test",
        "last_name": "Kullanıcı",
        "password": "Test123456",
        "is_staff": False,
    },
]

print("🔧 Test kullanıcıları oluşturuluyor...")
for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data["username"],
        defaults={
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "is_staff": user_data["is_staff"],
        },
    )
    user.set_password(user_data["password"])
    user.save()
    status = "oluşturuldu" if created else "güncellendi"
    print(f'✓ {user_data["username"]} kullanıcısı {status} - Staff: {user.is_staff}')

print("\n🔑 GİRİŞ BİLGİLERİ:")
print("=" * 40)
print("📋 PERSONEL (reviewer1):")
print("   Email: reviewer1@solutio360.com")
print("   Şifre: Test123456")
print("   URL: http://127.0.0.1:8000/accounts/login/")
print("")
print("👤 NORMAL KULLANICI (testuser):")
print("   Email: testuser@solutio360.com")
print("   Şifre: Test123456")
print("   URL: http://127.0.0.1:8000/accounts/login/")
