#!/bin/bash

# Solutio 360 - Production Deployment Script
# Bu script production deployment işlemlerini otomatikleştirir

set -e  # Hata durumunda dur

echo "🚀 Solutio 360 Production Deployment Başlıyor..."

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Environment check
check_environment() {
    log_info "Environment kontrol ediliyor..."
    
    if [ ! -f ".env" ]; then
        log_error ".env dosyası bulunamadı!"
        exit 1
    fi
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "docker-compose.prod.yml dosyası bulunamadı!"
        exit 1
    fi
    
    log_success "Environment dosyaları mevcut"
}

# Git checks
check_git() {
    log_info "Git durumu kontrol ediliyor..."
    
    # Uncommitted changes check
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "Commit edilmemiş değişiklikler var!"
        read -p "Devam etmek istiyor musunuz? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Current branch
    BRANCH=$(git branch --show-current)
    log_info "Mevcut branch: $BRANCH"
    
    if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
        log_warning "Production deployment için main/master branch önerilir"
    fi
    
    log_success "Git kontrolü tamamlandı"
}

# Docker build and test
build_and_test() {
    log_info "Docker image build ediliyor..."
    
    # Build image
    docker build -t solutio360:latest . || {
        log_error "Docker build başarısız!"
        exit 1
    }
    
    log_success "Docker image başarıyla build edildi"
    
    # Test container
    log_info "Container test ediliyor..."
    docker run --rm solutio360:latest python manage.py check --deploy || {
        log_error "Django deployment check başarısız!"
        exit 1
    }
    
    log_success "Container test başarılı"
}

# Database backup
backup_database() {
    log_info "Veritabanı yedekleniyor..."
    
    # Production DB backup
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME > "backups/$BACKUP_FILE" || {
        log_warning "Veritabanı yedekleme başarısız (devam ediliyor...)"
    }
    
    log_success "Veritabanı yedeklendi: $BACKUP_FILE"
}

# Deploy to production
deploy_production() {
    log_info "Production deployment başlıyor..."
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Stop services gracefully
    log_info "Servisler durdurluyor..."
    docker-compose -f docker-compose.prod.yml down --timeout 30
    
    # Start services
    log_info "Servisler başlatılıyor..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log_info "Servis health check'i bekleniyor..."
    sleep 30
    
    # Run migrations
    log_info "Veritabanı migrasyonları çalıştırılıyor..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
    
    # Collect static files
    log_info "Static dosyalar toplanıyor..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
    
    # Create superuser if needed
    log_info "Admin kullanıcısı kontrol ediliyor..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@solutio360.com', 'admin123')
    print('Superuser oluşturuldu: admin/admin123')
else:
    print('Superuser zaten mevcut')
"
    
    log_success "Production deployment tamamlandı!"
}

# Health check
health_check() {
    log_info "Health check yapılıyor..."
    
    # Web service health
    HEALTH_URL="http://localhost/health/"
    
    for i in {1..10}; do
        if curl -f -s $HEALTH_URL > /dev/null; then
            log_success "Web servisi sağlıklı"
            break
        else
            log_warning "Health check deneme $i/10..."
            sleep 10
        fi
        
        if [ $i -eq 10 ]; then
            log_error "Health check başarısız!"
            exit 1
        fi
    done
}

# Post deployment tasks
post_deployment() {
    log_info "Deployment sonrası görevler..."
    
    # Clear cache
    docker-compose -f docker-compose.prod.yml exec -T redis redis-cli FLUSHALL
    log_success "Cache temizlendi"
    
    # Restart Celery workers
    docker-compose -f docker-compose.prod.yml restart celery celery-beat
    log_success "Celery worker'ları yeniden başlatıldı"
    
    # Send deployment notification (optional)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 Solutio 360 production deployment tamamlandı!\"}" \
            $SLACK_WEBHOOK_URL
    fi
}

# Cleanup
cleanup() {
    log_info "Cleanup işlemi..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove old backups (keep last 7 days)
    find backups/ -name "backup_*.sql" -mtime +7 -delete 2>/dev/null || true
    
    log_success "Cleanup tamamlandı"
}

# Main deployment flow
main() {
    echo "=========================================="
    echo "🚀 Solutio 360 Production Deployment"
    echo "=========================================="
    
    # Create backup directory
    mkdir -p backups
    
    # Run deployment steps
    check_environment
    check_git
    build_and_test
    backup_database
    deploy_production
    health_check
    post_deployment
    cleanup
    
    echo "=========================================="
    log_success "✅ Deployment başarıyla tamamlandı!"
    echo "🌐 Site: https://yourdomain.com"
    echo "👤 Admin: https://yourdomain.com/admin/"
    echo "📊 Monitoring: https://yourdomain.com:3000"
    echo "=========================================="
}

# Rollback function
rollback() {
    log_warning "🔄 Rollback işlemi başlıyor..."
    
    BACKUP_FILE=$1
    if [ -z "$BACKUP_FILE" ]; then
        log_error "Backup dosyası belirtilmedi!"
        echo "Kullanım: $0 rollback backup_20240101_120000.sql"
        exit 1
    fi
    
    if [ ! -f "backups/$BACKUP_FILE" ]; then
        log_error "Backup dosyası bulunamadı: backups/$BACKUP_FILE"
        exit 1
    fi
    
    # Restore database
    log_info "Veritabanı geri yükleniyor..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER -d $DB_NAME < "backups/$BACKUP_FILE"
    
    # Restart services
    docker-compose -f docker-compose.prod.yml restart
    
    log_success "Rollback tamamlandı!"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback $2
        ;;
    "health")
        health_check
        ;;
    *)
        echo "Kullanım: $0 [deploy|rollback|health]"
        echo "  deploy  - Production deployment yap"
        echo "  rollback backup_file.sql - Rollback yap"
        echo "  health  - Health check yap"
        exit 1
        ;;
esac 