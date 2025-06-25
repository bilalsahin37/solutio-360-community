# =================================================================
# SOLUTIO 360 - Makefile
# =================================================================
# Django PWA Şikayet Yönetim Sistemi için geliştirici araçları

.PHONY: help install run test clean lint format security migrate collectstatic
.DEFAULT_GOAL := help

# =================================================================
# ENVIRONMENT VARIABLES
# =================================================================
PYTHON := python
PIP := pip
MANAGE := $(PYTHON) manage.py
PROJECT_NAME := solutio_360
VENV_NAME := venv
REQUIREMENTS := requirements.txt
REQUIREMENTS_DEV := requirements-dev.txt

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
PURPLE := \033[35m
CYAN := \033[36m
NC := \033[0m # No Color

# =================================================================
# HELP COMMANDS
# =================================================================
help: ## Bu yardım menüsünü gösterir
	@echo "$(CYAN)Solutio 360 - Django PWA Şikayet Yönetim Sistemi$(NC)"
	@echo "$(BLUE)=================================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Mevcut komutlar:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Örnek kullanım:$(NC)"
	@echo "  make install     # Bağımlılıkları kur"
	@echo "  make run         # Geliştirme sunucusunu başlat"
	@echo "  make test        # Testleri çalıştır"
	@echo "  make deploy      # Production'a deploy et"

# =================================================================
# DEVELOPMENT SETUP
# =================================================================
install: ## Proje bağımlılıklarını kurar
	@echo "$(BLUE)Bağımlılıklar kuruluyor...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r $(REQUIREMENTS)
	@if [ -f $(REQUIREMENTS_DEV) ]; then $(PIP) install -r $(REQUIREMENTS_DEV); fi
	@echo "$(GREEN)✓ Bağımlılıklar başarıyla kuruldu$(NC)"

venv: ## Virtual environment oluşturur
	@echo "$(BLUE)Virtual environment oluşturuluyor...$(NC)"
	$(PYTHON) -m venv $(VENV_NAME)
	@echo "$(GREEN)✓ Virtual environment oluşturuldu$(NC)"
	@echo "$(YELLOW)Aktivasyon: source $(VENV_NAME)/bin/activate$(NC)"

setup: venv install migrate collectstatic ## Tam kurulum yapar
	@echo "$(GREEN)✓ Proje kurulumu tamamlandı$(NC)"

# =================================================================
# DATABASE OPERATIONS
# =================================================================
migrate: ## Database migrasyonlarını uygular
	@echo "$(BLUE)Migrasyonlar uygulanıyor...$(NC)"
	$(MANAGE) makemigrations
	$(MANAGE) migrate
	@echo "$(GREEN)✓ Migrasyonlar tamamlandı$(NC)"

makemigrations: ## Yeni migrasyonlar oluşturur
	@echo "$(BLUE)Yeni migrasyonlar oluşturuluyor...$(NC)"
	$(MANAGE) makemigrations
	@echo "$(GREEN)✓ Migrasyonlar oluşturuldu$(NC)"

reset-db: ## Database'i sıfırlar (DİKKAT!)
	@echo "$(RED)⚠️  Database sıfırlanacak! Devam etmek istiyor musunuz? [y/N]$(NC)"
	@read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		echo "$(BLUE)Database sıfırlanıyor...$(NC)"; \
		rm -f db.sqlite3; \
		$(MANAGE) migrate; \
		echo "$(GREEN)✓ Database sıfırlandı$(NC)"; \
	else \
		echo "$(YELLOW)İşlem iptal edildi$(NC)"; \
	fi

seed-db: ## Test verileri ekler
	@echo "$(BLUE)Test verileri ekleniyor...$(NC)"
	$(MANAGE) loaddata fixtures/initial_data.json || echo "Fixture dosyası bulunamadı"
	@echo "$(GREEN)✓ Test verileri eklendi$(NC)"

# =================================================================
# SERVER OPERATIONS
# =================================================================
run: ## Geliştirme sunucusunu başlatır
	@echo "$(BLUE)Geliştirme sunucusu başlatılıyor...$(NC)"
	$(MANAGE) runserver

run-prod: ## Production modda sunucu başlatır
	@echo "$(BLUE)Production sunucu başlatılıyor...$(NC)"
	DEBUG=False $(MANAGE) runserver --settings=solutio_360.settings.production

shell: ## Django shell açar
	@echo "$(BLUE)Django shell açılıyor...$(NC)"
	$(MANAGE) shell

superuser: ## Superuser oluşturur
	@echo "$(BLUE)Superuser oluşturuluyor...$(NC)"
	$(MANAGE) createsuperuser

# =================================================================
# STATIC FILES
# =================================================================
collectstatic: ## Static dosyaları toplar
	@echo "$(BLUE)Static dosyalar toplanıyor...$(NC)"
	$(MANAGE) collectstatic --noinput
	@echo "$(GREEN)✓ Static dosyalar toplandı$(NC)"

compress: ## CSS/JS dosyalarını sıkıştırır
	@echo "$(BLUE)Assets sıkıştırılıyor...$(NC)"
	$(MANAGE) compress --force
	@echo "$(GREEN)✓ Assets sıkıştırıldı$(NC)"

# =================================================================
# TESTING
# =================================================================
test: ## Tüm testleri çalıştırır
	@echo "$(BLUE)Testler çalıştırılıyor...$(NC)"
	$(PYTHON) -m pytest -v --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Testler tamamlandı$(NC)"

test-unit: ## Unit testleri çalıştırır
	@echo "$(BLUE)Unit testler çalıştırılıyor...$(NC)"
	$(PYTHON) -m pytest -v -m "unit" --cov=. --cov-report=term
	@echo "$(GREEN)✓ Unit testler tamamlandı$(NC)"

test-integration: ## Integration testleri çalıştırır
	@echo "$(BLUE)Integration testler çalıştırılıyor...$(NC)"
	$(PYTHON) -m pytest -v -m "integration" --cov=. --cov-report=term
	@echo "$(GREEN)✓ Integration testler tamamlandı$(NC)"

test-coverage: ## Test coverage raporu oluşturur
	@echo "$(BLUE)Coverage raporu oluşturuluyor...$(NC)"
	$(PYTHON) -m pytest --cov=. --cov-report=html --cov-report=xml
	@echo "$(GREEN)✓ Coverage raporu hazır: htmlcov/index.html$(NC)"

# =================================================================
# CODE QUALITY
# =================================================================
lint: ## Kod kalitesi kontrolü yapar
	@echo "$(BLUE)Lint kontrolü yapılıyor...$(NC)"
	black . --check --diff
	isort . --check-only --diff
	flake8 .
	mypy .
	@echo "$(GREEN)✓ Lint kontrolü tamamlandı$(NC)"

format: ## Kodu otomatik formatlar
	@echo "$(BLUE)Kod formatlanıyor...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✓ Kod formatlandı$(NC)"

format-check: ## Format kontrolü yapar
	@echo "$(BLUE)Format kontrolü yapılıyor...$(NC)"
	black . --check
	isort . --check-only
	@echo "$(GREEN)✓ Format kontrolü tamamlandı$(NC)"

# =================================================================
# SECURITY
# =================================================================
security: ## Güvenlik kontrolü yapar
	@echo "$(BLUE)Güvenlik kontrolü yapılıyor...$(NC)"
	safety check
	bandit -r . -x /venv/,/env/,*/migrations/,*/tests/
	$(MANAGE) check --deploy
	@echo "$(GREEN)✓ Güvenlik kontrolü tamamlandı$(NC)"

check: ## Django sistem kontrolü yapar
	@echo "$(BLUE)Sistem kontrolü yapılıyor...$(NC)"
	$(MANAGE) check
	@echo "$(GREEN)✓ Sistem kontrolü tamamlandı$(NC)"

# =================================================================
# DEPENDENCIES
# =================================================================
requirements: ## Requirements.txt günceller
	@echo "$(BLUE)Requirements güncelleniyor...$(NC)"
	$(PIP) freeze > $(REQUIREMENTS)
	@echo "$(GREEN)✓ Requirements güncellendi$(NC)"

upgrade: ## Bağımlılıkları günceller
	@echo "$(BLUE)Bağımlılıklar güncelleniyor...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -U -r $(REQUIREMENTS)
	@echo "$(GREEN)✓ Bağımlılıklar güncellendi$(NC)"

# =================================================================
# DOCKER OPERATIONS
# =================================================================
docker-build: ## Docker image oluşturur
	@echo "$(BLUE)Docker image oluşturuluyor...$(NC)"
	docker build -t $(PROJECT_NAME):latest .
	@echo "$(GREEN)✓ Docker image oluşturuldu$(NC)"

docker-run: ## Docker container çalıştırır
	@echo "$(BLUE)Docker container çalıştırılıyor...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Docker container çalışıyor$(NC)"

docker-stop: ## Docker container'ları durdurur
	@echo "$(BLUE)Docker container'lar durduruluyor...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Docker container'lar durduruldu$(NC)"

docker-logs: ## Docker loglarını gösterir
	@echo "$(BLUE)Docker logları gösteriliyor...$(NC)"
	docker-compose logs -f

docker-clean: ## Docker temizliği yapar
	@echo "$(BLUE)Docker temizliği yapılıyor...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)✓ Docker temizliği tamamlandı$(NC)"

# =================================================================
# CELERY OPERATIONS
# =================================================================
celery-worker: ## Celery worker başlatır
	@echo "$(BLUE)Celery worker başlatılıyor...$(NC)"
	celery -A $(PROJECT_NAME) worker --loglevel=info

celery-beat: ## Celery beat başlatır
	@echo "$(BLUE)Celery beat başlatılıyor...$(NC)"
	celery -A $(PROJECT_NAME) beat --loglevel=info

celery-flower: ## Celery flower başlatır
	@echo "$(BLUE)Celery flower başlatılıyor...$(NC)"
	celery -A $(PROJECT_NAME) flower

celery-purge: ## Celery queue'ları temizler
	@echo "$(BLUE)Celery queue'lar temizleniyor...$(NC)"
	celery -A $(PROJECT_NAME) purge -f
	@echo "$(GREEN)✓ Celery queue'lar temizlendi$(NC)"

# =================================================================
# DEPLOYMENT
# =================================================================
deploy-staging: ## Staging ortamına deploy eder
	@echo "$(BLUE)Staging'e deploy ediliyor...$(NC)"
	@echo "$(YELLOW)Bu işlem henüz yapılandırılmamış$(NC)"

deploy-production: ## Production ortamına deploy eder
	@echo "$(BLUE)Production'a deploy ediliyor...$(NC)"
	@echo "$(RED)⚠️  Production deploy işlemi dikkatli yapılmalıdır!$(NC)"
	@echo "$(YELLOW)Bu işlem henüz yapılandırılmamış$(NC)"

backup-db: ## Database backup alır
	@echo "$(BLUE)Database backup alınıyor...$(NC)"
	$(MANAGE) dumpdata > backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "$(GREEN)✓ Database backup alındı$(NC)"

# =================================================================
# CLEANUP
# =================================================================
clean: ## Geçici dosyaları temizler
	@echo "$(BLUE)Temizlik yapılıyor...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "htmlcov" -delete
	find . -type f -name "coverage.xml" -delete
	@echo "$(GREEN)✓ Temizlik tamamlandı$(NC)"

clean-all: clean ## Tüm geçici dosyaları ve cache'i temizler
	@echo "$(BLUE)Tam temizlik yapılıyor...$(NC)"
	rm -rf staticfiles/
	rm -rf media/uploaded_files/
	rm -rf logs/*.log
	@echo "$(GREEN)✓ Tam temizlik tamamlandı$(NC)"

# =================================================================
# MONITORING
# =================================================================
logs: ## Uygulama loglarını gösterir
	@echo "$(BLUE)Loglar gösteriliyor...$(NC)"
	tail -f logs/solutio_360.log

status: ## Sistem durumunu kontrol eder
	@echo "$(BLUE)Sistem durumu kontrol ediliyor...$(NC)"
	@echo "$(YELLOW)Python Version:$(NC) $(shell $(PYTHON) --version)"
	@echo "$(YELLOW)Django Version:$(NC) $(shell $(MANAGE) --version)"
	@echo "$(YELLOW)Database Status:$(NC)"
	@$(MANAGE) showmigrations | grep -c "\[X\]" || echo "0"
	@echo "$(GREEN)✓ Sistem durumu kontrol edildi$(NC)"

# =================================================================
# DEVELOPMENT UTILITIES
# =================================================================
shell-plus: ## Django shell_plus açar (django-extensions gerekli)
	@echo "$(BLUE)Django shell_plus açılıyor...$(NC)"
	$(MANAGE) shell_plus

graph-models: ## Model grafiklerini oluşturur
	@echo "$(BLUE)Model grafikleri oluşturuluyor...$(NC)"
	$(MANAGE) graph_models -a -g -o models.png
	@echo "$(GREEN)✓ Model grafikleri oluşturuldu: models.png$(NC)"

runserver-plus: ## Django runserver_plus başlatır
	@echo "$(BLUE)Enhanced development server başlatılıyor...$(NC)"
	$(MANAGE) runserver_plus 