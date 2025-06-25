# Solutio 360 - Şikayet Yönetim Sistemi

Modern, güvenli ve kullanıcı dostu Progressive Web App (PWA) olarak geliştirilen şikayet yönetim sistemi.

## 🚀 Özellikler

### Temel Özellikler
- **Şikayet Yönetimi**: Şikayet oluşturma, takip etme ve çözüm süreçleri
- **Kullanıcı Yönetimi**: Rol bazlı yetkilendirme sistemi
- **Raporlama**: Detaylı analitik ve raporlama araçları
- **Bildirim Sistemi**: Real-time bildirimler ve email entegrasyonu

### PWA Özellikleri
- **Offline Çalışma**: Service Worker ile offline desteği
- **App Install**: Mobil cihazlara yüklenebilir
- **Push Bildirimleri**: Gerçek zamanlı bildirimler
- **Responsive Tasarım**: Tüm cihazlarda uyumlu

### Teknoloji Stack
- **Backend**: Django 5.2.2, Python 3.11+
- **Frontend**: Tailwind CSS, JavaScript ES6+
- **Database**: SQLite (geliştirme), PostgreSQL (production)
- **Cache**: Redis
- **Queue**: Celery
- **PWA**: Service Worker, Web App Manifest

## 📋 Gereksinimler

- Python 3.11+
- Django 5.2.2
- Node.js 18+ (frontend build için)
- Redis (cache ve celery için)
- PostgreSQL (production için)

## 🛠️ Kurulum

### 1. Projeyi Klonlama
```bash
git clone <repo-url>
cd solutio_360
```

### 2. Virtual Environment Oluşturma
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları Yükleme
```bash
pip install -r requirements.txt
```

### 4. Environment Değişkenleri
`.env` dosyası oluşturun:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Veritabanı Migrasyonları
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Superuser Oluşturma
```bash
python manage.py createsuperuser
```

### 7. Static Dosyları Toplama
```bash
python manage.py collectstatic
```

### 8. Sunucuyu Başlatma
```bash
python manage.py runserver
```

## 🎯 Kullanım

### Yönetici Paneli
- **URL**: http://localhost:8000/admin/
- **Özellikler**: 
  - Kullanıcı yönetimi
  - Şikayet kategorileri
  - Sistem ayarları
  - Raporlar

### Ana Uygulama
- **URL**: http://localhost:8000/
- **Giriş**: Kayıtlı kullanıcı bilgileri ile
- **Özellikler**:
  - Şikayet oluşturma
  - Şikayet takibi
  - Dashboard
  - Raporlar

### API Endpoints
- **Base URL**: http://localhost:8000/api/
- **Swagger**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## 📱 PWA Kullanımı

### Yükleme
1. Uygulamayı web tarayıcısında açın
2. Tarayıcıda "Ana ekrana ekle" seçeneğini kullanın
3. Veya uygulama içindeki install banner'ını kullanın

### Offline Kullanım
- Daha önce görüntülenen sayfalar offline erişilebilir
- Offline oluşturulan veriler otomatik sync edilir
- Cache stratejisi ile hızlı yükleme

## 🔧 Geliştirme

### Proje Yapısı
```
solutio_360/
├── complaints/          # Şikayet modülü
├── core/               # Temel modül
├── reports/            # Raporlama modülü
├── users/              # Kullanıcı modülü
├── static/             # Static dosyalar
├── templates/          # Template dosyalar
├── media/              # Media dosyalar
└── solutio_360/        # Ana proje ayarları
```

### Kod Standartları
- **PEP 8**: Python kod standardı
- **Black**: Kod formatlaması
- **flake8**: Linting
- **mypy**: Type checking

### Test Etme
```bash
# Tüm testleri çalıştır
python manage.py test

# Coverage raporu
coverage run --source='.' manage.py test
coverage html
```

### Linting ve Formatting
```bash
# Black ile formatlama
black .

# flake8 ile linting
flake8 .

# isort ile import sıralama
isort .
```

## 🚀 Deployment

### Production Ayarları
1. `DEBUG = False` yapın
2. `ALLOWED_HOSTS` ayarlayın
3. PostgreSQL veritabanı yapılandırın
4. Redis yapılandırın
5. Email ayarlarını yapın
6. SSL sertifikası ekleyin

### Docker ile Deployment
```bash
# Docker container oluştur
docker build -t solutio360 .

# Çalıştır
docker run -p 8000:8000 solutio360
```

### Heroku ile Deployment
```bash
# Heroku CLI kurulu olmalı
heroku create solutio360-app
git push heroku main
heroku run python manage.py migrate
```

## 📊 Monitoring ve Analytics

### Sistem Metrikleri
- User aktiviteleri
- Şikayet istatistikleri
- Performans metrikleri
- Error tracking

### Loglar
- Application logs: `logs/solutio_360.log`
- Error logs: Console ve file
- Audit logs: Database

## 🔒 Güvenlik

### Güvenlik Özellikleri
- **CSRF Protection**: Django built-in
- **SQL Injection**: ORM kullanımı
- **XSS Protection**: Template escaping
- **Authentication**: Django auth system
- **Authorization**: Role-based permissions

### KVKV Uyumluluk
- Kişisel veri şifreleme
- Veri silme hakları
- Consent yönetimi
- Audit trail

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'i push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📞 İletişim

- **Email**: info@solutio360.com
- **Website**: https://solutio360.com
- **Issues**: GitHub Issues

## 🎯 Roadmap

### v1.1
- [ ] AI-powered şikayet kategorilendirme
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)

### v1.2
- [ ] Multi-tenant architecture
- [ ] Advanced reporting
- [ ] Integration API'lar

### v1.3
- [ ] Workflow automation
- [ ] Advanced notifications
- [ ] Performance optimizations

## 📈 Changelog

### v1.0.0 (Current)
- İlk kararlı sürüm
- Temel şikayet yönetimi
- PWA özellikleri
- Kullanıcı yönetimi
- Raporlama sistemi

---

**Solutio 360** - Modern Şikayet Yönetim Sistemi 