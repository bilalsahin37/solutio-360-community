# Solutio 360 - Deployment Rehberi

Bu belge, Solutio 360 PWA uygulamasının farklı ortamlarda nasıl deploy edileceğini anlatır.

## 📋 Ön Gereksinimler

### Sistem Gereksinimleri
- **Python**: 3.11 veya üzeri
- **Node.js**: 18 veya üzeri (frontend build için)
- **Database**: PostgreSQL 14+ (production)
- **Cache**: Redis 6+
- **Web Server**: Nginx veya Apache
- **SSL Certificate**: Let's Encrypt veya commercial

### Gerekli Servisler
- **Email**: SMTP server (Gmail, SendGrid, vb.)
- **Storage**: Local filesystem veya Cloud (AWS S3, Azure Blob)
- **Monitoring**: Sentry (error tracking)
- **Analytics**: Google Analytics (opsiyonel)

## 🌟 Production Deployment

### 1. Sunucu Hazırlığı (Ubuntu 22.04)

```bash
# Sistem güncellemesi
sudo apt update && sudo apt upgrade -y

# Python ve dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install build-essential libpq-dev postgresql-client

# Nginx ve Redis
sudo apt install nginx redis-server

# PostgreSQL
sudo apt install postgresql postgresql-contrib

# Node.js (frontend build için)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Git
sudo apt install git
```

### 2. Database Kurulumu

```bash
# PostgreSQL kullanıcı ve database oluştur
sudo -u postgres psql
```

```sql
CREATE USER solutio360 WITH PASSWORD 'güvenli_şifre';
CREATE DATABASE solutio360_db OWNER solutio360;
GRANT ALL PRIVILEGES ON DATABASE solutio360_db TO solutio360;
ALTER USER solutio360 CREATEDB;
\q
```

### 3. Uygulama Kurulumu

```bash
# Uygulama dizini oluştur
sudo mkdir -p /var/www/solutio360
sudo chown $USER:$USER /var/www/solutio360

# Projeyi klonla
cd /var/www/solutio360
git clone <repository-url> .

# Virtual environment oluştur
python3.11 -m venv venv
source venv/bin/activate

# Dependencies yükle
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Frontend build (eğer gerekiyorsa)
npm install
npm run build
```

### 4. Environment Konfigürasyonu

`.env` dosyası oluştur:

```env
# Django Settings
DEBUG=False
SECRET_KEY=süper_güvenli_secret_key_buraya
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://solutio360:şifre@localhost:5432/solutio360_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-specific-password
EMAIL_USE_TLS=True

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Monitoring
SENTRY_DSN=https://your-sentry-dsn

# Static/Media
STATIC_ROOT=/var/www/solutio360/staticfiles
MEDIA_ROOT=/var/www/solutio360/media
```

### 5. Django Konfigürasyonu

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Static files
python manage.py collectstatic --noinput

# Superuser oluştur
python manage.py createsuperuser

# Test
python manage.py check --deploy
```

### 6. Gunicorn Konfigürasyonu

`gunicorn.conf.py` oluştur:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "www-data"
group = "www-data"
tmp_upload_dir = None
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"
```

Systemd service dosyası `/etc/systemd/system/solutio360.service`:

```ini
[Unit]
Description=Solutio 360 Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/solutio360
ExecStart=/var/www/solutio360/venv/bin/gunicorn -c gunicorn.conf.py solutio_360.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Service'i başlat:

```bash
sudo systemctl daemon-reload
sudo systemctl start solutio360
sudo systemctl enable solutio360
```

### 7. Nginx Konfigürasyonu

`/etc/nginx/sites-available/solutio360` dosyası:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # PWA Headers
    add_header Service-Worker-Allowed "/";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/solutio360/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    location /media/ {
        alias /var/www/solutio360/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # PWA Files
    location = /manifest.json {
        alias /var/www/solutio360/staticfiles/manifest.json;
        add_header Content-Type application/manifest+json;
        expires 1y;
    }

    location = /sw.js {
        alias /var/www/solutio360/staticfiles/js/sw.js;
        add_header Content-Type application/javascript;
        expires 0;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types application/javascript application/json application/xml text/css text/javascript text/plain text/xml;

    client_max_body_size 100M;
}
```

Site'i aktifleştir:

```bash
sudo ln -s /etc/nginx/sites-available/solutio360 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Sertifikası (Let's Encrypt)

```bash
# Certbot kurulumu
sudo apt install certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

### 9. Celery Konfigürasyonu (Background Tasks)

Celery worker service `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/var/www/solutio360/.env
WorkingDirectory=/var/www/solutio360
ExecStart=/var/www/solutio360/venv/bin/celery multi start worker1 \
    -A solutio_360 --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log --loglevel=INFO
ExecStop=/var/www/solutio360/venv/bin/celery multi stopwait worker1 \
    --pidfile=/var/run/celery/%n.pid
ExecReload=/var/www/solutio360/venv/bin/celery multi restart worker1 \
    -A solutio_360 --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log --loglevel=INFO

[Install]
WantedBy=multi-user.target
```

Celery beat service `/etc/systemd/system/celerybeat.service`:

```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
EnvironmentFile=/var/www/solutio360/.env
WorkingDirectory=/var/www/solutio360
ExecStart=/var/www/solutio360/venv/bin/celery -A solutio_360 beat \
    --loglevel=INFO --pidfile=/var/run/celery/beat.pid \
    --schedule=/var/run/celery/celerybeat-schedule

[Install]
WantedBy=multi-user.target
```

Dizinleri oluştur ve servisleri başlat:

```bash
sudo mkdir -p /var/run/celery /var/log/celery
sudo chown www-data:www-data /var/run/celery /var/log/celery

sudo systemctl daemon-reload
sudo systemctl start celery celerybeat
sudo systemctl enable celery celerybeat
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "solutio_360.wsgi:application"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://solutio360:password@db:5432/solutio360_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: solutio360_db
      POSTGRES_USER: solutio360
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

## ☁️ Cloud Deployment

### Heroku

1. Heroku CLI kurulumu
2. `Procfile` oluştur:
```
web: gunicorn solutio_360.wsgi:application
worker: celery -A solutio_360 worker -l info
beat: celery -A solutio_360 beat -l info
```

3. Deploy:
```bash
heroku create solutio360-app
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
heroku config:set DEBUG=False
git push heroku main
heroku run python manage.py migrate
```

### AWS EC2 + RDS

1. EC2 instance oluştur (Ubuntu 22.04)
2. RDS PostgreSQL instance oluştur
3. ElastiCache Redis cluster oluştur
4. Security groups ayarla
5. Yukarıdaki production adımlarını takip et

## 📊 Monitoring ve Maintenance

### 1. Log Monitoring

```bash
# Application logs
tail -f /var/log/gunicorn/error.log
tail -f /var/log/celery/worker1.log

# System logs
journalctl -u solutio360 -f
journalctl -u nginx -f
```

### 2. Performance Monitoring

New Relic veya Datadog entegrasyonu:

```python
# settings.py
if not DEBUG:
    import newrelic.agent
    newrelic.agent.initialize('/path/to/newrelic.ini')
```

### 3. Backup Strategy

Database backup scripti:

```bash
#!/bin/bash
# /etc/cron.daily/solutio360-backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/solutio360"

# Database backup
pg_dump -h localhost -U solutio360 solutio360_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/solutio360/media/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### 4. Update Process

```bash
#!/bin/bash
# Update script

cd /var/www/solutio360
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart solutio360
sudo systemctl restart celery
sudo systemctl restart celerybeat
```

## 🔒 Security Checklist

- [ ] SSL certificate kuruldu
- [ ] Firewall yapılandırıldı (UFW)
- [ ] Database encryption aktif
- [ ] Backup sistemı çalışıyor
- [ ] Monitoring aktif
- [ ] Log rotation yapılandırıldı
- [ ] Security headers eklendi
- [ ] Rate limiting aktif
- [ ] Admin panel IP kısıtlaması
- [ ] SSH key authentication
- [ ] Fail2ban kuruldu

## 📞 Troubleshooting

### Yaygın Problemler

1. **Static files yüklenmiyor**
   - `python manage.py collectstatic --noinput`
   - Nginx konfigürasyonunu kontrol et

2. **Database bağlantı hatası**
   - PostgreSQL servisini kontrol et
   - `.env` dosyasındaki DATABASE_URL'i kontrol et

3. **Celery çalışmıyor**
   - Redis bağlantısını kontrol et
   - Celery log dosyalarını incele

4. **SSL sertifikası hatası**
   - Certbot yenileme: `sudo certbot renew`
   - Nginx konfigürasyonunu test et

## 📚 Kaynaklar

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Celery Documentation](https://docs.celeryproject.org/) 