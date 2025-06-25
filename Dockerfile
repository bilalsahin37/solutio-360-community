# Solutio 360 - Production Docker Konfigürasyonu
# Multi-stage build kullanarak optimize edilmiş image

# Stage 1: Dependencies Builder
FROM python:3.11-slim as builder

# Sistem güncellemeleri ve build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Solutio 360 Team"
LABEL description="Solutio 360 PWA - Şikayet Yönetim Sistemi"
LABEL version="1.0.0"

# Güvenlik için non-root user oluştur
RUN groupadd -r solutio && useradd -r -g solutio solutio

# Sistem dependencies (sadece runtime)
RUN apt-get update && apt-get install -y \
    libpq5 \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies'leri builder'dan kopyala
COPY --from=builder /root/.local /home/solutio/.local

# Uygulama dizini oluştur
WORKDIR /app

# Uygulama kodunu kopyala
COPY . .

# Ownership'i solutio user'a ver
RUN chown -R solutio:solutio /app

# Static files dizini
RUN mkdir -p /app/staticfiles && chown solutio:solutio /app/staticfiles

# Media files dizini
RUN mkdir -p /app/media && chown solutio:solutio /app/media

# Logs dizini
RUN mkdir -p /app/logs && chown solutio:solutio /app/logs

# Python path
ENV PATH=/home/solutio/.local/bin:$PATH

# Django settings
ENV DJANGO_SETTINGS_MODULE=solutio_360.settings
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Production environment
ENV DEBUG=False
ENV ENVIRONMENT=production

# User switch
USER solutio

# Static files topla
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py check --deploy || exit 1

# Port expose
EXPOSE 8000

# Production server için gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "--log-level", "info", "solutio_360.wsgi:application"] 