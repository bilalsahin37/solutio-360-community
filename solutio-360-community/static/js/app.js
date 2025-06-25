/**
 * Solutio 360 - Ana Uygulama Kontrolcüsü
 * ======================================
 * 
 * Bu dosya Solutio 360 PWA uygulamasının ana JavaScript modülüdür.
 * Tüm frontend işlevselliğini koordine eder ve yönetir.
 * 
 * Ana sorumlulukları:
 * - Uygulama başlatma ve yapılandırma
 * - Modül yönetimi (PWA, tema, form, modal vb.)
 * - Global event handling
 * - Network durumu takibi
 * - Offline veri senkronizasyonu
 * - Error handling ve logging
 */

class Solutio360App {
    constructor() {
        this.version = '1.0.0';          // Uygulama versiyonu
        this.modules = {};               // Yüklenen modüller
        
        // Uygulama konfigürasyonu
        this.config = {
            apiBaseUrl: '/api/',         // API base URL'si
            refreshInterval: 30000,      // Veri yenileme aralığı (30 saniye)
            maxRetries: 3,              // Maksimum yeniden deneme sayısı
            retryDelay: 1000,           // Yeniden deneme gecikmesi (1 saniye)
            cacheTimeout: 300000,       // Cache timeout (5 dakika)
        };
        
        // Uygulamayı başlat
        this.init();
    }

    /**
     * Uygulamayı başlatma işlemi.
     * 
     * DOM hazır olmasını bekler ve gerekli başlatma işlemlerini yapar.
     * Bu fonksiyon uygulama lifecycle'ının başlangıç noktasıdır.
     */
    init() {
        console.log(`[App] Solutio 360 v${this.version} başlatılıyor...`);
        
        // DOM ready kontrolü - sayfa tamamen yüklenene kadar bekle
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.onDOMReady();
            });
        } else {
            // DOM zaten hazırsa direkt başlat
            this.onDOMReady();
        }
    }

    /**
     * DOM hazır olduğunda çalışacak ana işlemler.
     * 
     * Tüm modülleri başlatır ve event listener'ları kurar.
     * Uygulama architecture'ının merkezindeki fonksiyondur.
     */
    onDOMReady() {
        console.log('[App] DOM hazır, modüller yükleniyor...');
        
        // Temel modülleri sırayla başlat
        this.initCoreModules();
        
        // Sayfa özel modülleri başlat
        this.initPageModules();
        
        // Global event listener'ları kur
        this.setupGlobalEventListeners();
        
        // Performans izleme başlat
        this.setupPerformanceMonitoring();
        
        console.log('[App] Solutio 360 başarıyla başlatıldı');
    }

    /**
     * Temel modülleri başlatma.
     * 
     * Uygulamanın her sayfasında kullanılan core modülleri yükler.
     * Bu modüller uygulama genelinde aktif olurlar.
     */
    initCoreModules() {
        // PWA Manager - Progressive Web App işlevleri
        if (typeof PWAManager !== 'undefined') {
            this.modules.pwa = new PWAManager();
        }

        // Theme Manager - Karanlık/aydınlık mod yönetimi
        this.modules.theme = new ThemeManager();
        
        // Notification Manager - Bildirim sistemi
        if (typeof NotificationManager !== 'undefined') {
            this.modules.notifications = new NotificationManager();
        }

        // Form Manager - Form validasyonu ve AJAX işlemleri
        this.modules.forms = new FormManager();
        
        // Modal Manager - Modal pencere yönetimi
        this.modules.modals = new ModalManager();
        
        // Search Manager - Global arama işlemleri
        this.modules.search = new SearchManager();
    }

    /**
     * Sayfa özel modüllerini başlatma.
     * 
     * Mevcut sayfaya göre gerekli modülleri yükler.
     * Bu yaklaşım sayfa yükleme performansını artırır.
     */
    initPageModules() {
        const currentPage = this.getCurrentPage();
        
        switch (currentPage) {
            case 'dashboard':
                // Dashboard sayfası için özel modül
                if (typeof DashboardManager !== 'undefined') {
                    this.modules.dashboard = new DashboardManager();
                }
                break;
                
            case 'complaints':
                // Şikayet sayfaları için özel modül
                if (typeof ComplaintManager !== 'undefined') {
                    this.modules.complaints = new ComplaintManager();
                }
                break;
                
            case 'reports':
                // Rapor sayfaları için özel modül
                if (typeof ReportManager !== 'undefined') {
                    this.modules.reports = new ReportManager();
                }
                break;
                
            case 'analytics':
                // Analitik sayfası için özel modül
                if (typeof AnalyticsManager !== 'undefined') {
                    this.modules.analytics = new AnalyticsManager();
                }
                break;
        }
    }

    /**
     * Mevcut sayfayı belirleme.
     * 
     * URL path'ini analiz ederek hangi sayfada olduğumuzu belirler.
     * Bu bilgi sayfa özel modüllerin yüklenmesi için kullanılır.
     * 
     * @returns {string} Sayfa adı
     */
    getCurrentPage() {
        const path = window.location.pathname;
        
        if (path.includes('/dashboard')) return 'dashboard';
        if (path.includes('/complaints')) return 'complaints';
        if (path.includes('/reports')) return 'reports';
        if (path.includes('/analytics')) return 'analytics';
        
        return 'home';
    }

    /**
     * Global event listener'ları kurma.
     * 
     * Uygulama genelinde geçerli olacak event'leri dinler:
     * - Network durumu değişiklikleri
     * - Sayfa görünürlük değişiklikleri
     * - Hata yakalama
     * - Keyboard shortcut'ları
     */
    setupGlobalEventListeners() {
        // Network durumu izleme - online/offline detection
        window.addEventListener('online', () => {
            this.handleNetworkChange(true);
        });
        
        window.addEventListener('offline', () => {
            this.handleNetworkChange(false);
        });

        // Page Visibility API - sayfa aktif/inaktif durumu
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });

        // Sayfa kapatma/yenileme öncesi işlemler
        window.addEventListener('beforeunload', () => {
            this.handleBeforeUnload();
        });

        // Global hata yakalama
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event);
        });

        // Global klavye kısayolları
        document.addEventListener('keydown', (event) => {
            this.handleGlobalKeyboard(event);
        });

        // AJAX hata yönetimi kurulumu
        this.setupAjaxErrorHandling();
    }

    /**
     * Network durumu değişikliği yönetimi.
     * 
     * İnternet bağlantısı kesilip bağlandığında gerekli işlemleri yapar.
     * Offline veri senkronizasyonu ve kullanıcı bildirimi.
     * 
     * @param {boolean} isOnline - Online durumu
     */
    handleNetworkChange(isOnline) {
        console.log(`[App] Network durumu: ${isOnline ? 'Online' : 'Offline'}`);
        
        if (isOnline) {
            // Online olduğunda
            this.showToast('İnternet bağlantısı yeniden kuruldu', 'success');
            this.syncOfflineData(); // Offline verileri sync et
        } else {
            // Offline olduğunda
            this.showToast('İnternet bağlantısı kesildi', 'warning');
        }
        
        // Tüm modüllere network durumu değişikliğini bildir
        Object.values(this.modules).forEach(module => {
            if (module.handleNetworkChange) {
                module.handleNetworkChange(isOnline);
            }
        });
    }

    /**
     * Sayfa görünürlük değişikliği yönetimi.
     * 
     * Sayfa aktif/inaktif olduğunda gerekli optimizasyonları yapar.
     * Periyodik görevleri duraklat/devam ettir.
     */
    handleVisibilityChange() {
        if (document.hidden) {
            console.log('[App] Sayfa gizlendi');
            this.pausePeriodicTasks();        // Periyodik görevleri duraklat
        } else {
            console.log('[App] Sayfa görünür oldu');
            this.resumePeriodicTasks();       // Periyodik görevleri devam ettir
            this.refreshData();               // Verileri yenile
        }
    }

    /**
     * Sayfa kapatma/yenileme öncesi işlemler.
     * 
     * Kullanıcı sayfayı kapatmadan önce:
     * - Kaydedilmemiş verileri kaydet
     * - Temizlik işlemleri yap
     * - Analytics verileri gönder
     */
    handleBeforeUnload() {
        console.log('[App] Sayfa kapatılıyor, temizlik işlemleri yapılıyor...');
        
        // Kaydedilmemiş form verilerini local storage'a kaydet
        this.saveUnsavedData();
        
        // Analytics verileri gönder
        if (this.modules.analytics) {
            this.modules.analytics.sendPendingData();
        }
        
        // Aktif network request'leri iptal et
        if (this.pendingRequests) {
            this.pendingRequests.forEach(request => {
                if (request.abort) request.abort();
            });
        }
    }

    /**
     * Global hata yönetimi.
     * 
     * Yakalanmamış JavaScript hatalarını merkezi olarak yönetir.
     * Hata raporlama ve kullanıcı bilgilendirmesi.
     * 
     * @param {ErrorEvent} event - Hata event'i
     */
    handleGlobalError(event) {
        console.error('[App] Global hata yakalandı:', event.error);
        
        // Hata detaylarını topla
        const errorInfo = {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error ? event.error.stack : null,
            userAgent: navigator.userAgent,
            url: window.location.href,
            timestamp: new Date().toISOString()
        };
        
        // Hata raporlama servisine gönder
        this.reportError(errorInfo);
        
        // Kullanıcıya bilgilendirici mesaj göster
        this.showToast('Beklenmeyen bir hata oluştu', 'error');
    }

    /**
     * Global klavye kısayolları yönetimi.
     * 
     * Uygulama genelindeki klavye kısayollarını işler.
     * 
     * @param {KeyboardEvent} event - Klavye event'i
     */
    handleGlobalKeyboard(event) {
        // Ctrl/Cmd tuşu kombinasyonları
        const isCtrlPressed = event.ctrlKey || event.metaKey;
        
        if (isCtrlPressed) {
            switch (event.key) {
                case 'k':
                    // Ctrl+K: Arama açma
                    event.preventDefault();
                    this.focusSearch();
                    break;
                    
                case 's':
                    // Ctrl+S: Form kaydetme
                    event.preventDefault();
                    this.saveCurrentForm();
                    break;
                    
                case 'e':
                    // Ctrl+E: Dashboard'a git
                    event.preventDefault();
                    window.location.href = '/dashboard/';
                    break;
            }
        }
        
        // Escape tuşu - modal'ları kapat
        if (event.key === 'Escape') {
            this.closeModals();
        }
        
        // F1 tuşu - yardım
        if (event.key === 'F1') {
            event.preventDefault();
            this.showKeyboardShortcuts();
        }
    }

    /**
     * Ajax hata yönetimi
     */
    setupAjaxErrorHandling() {
        // jQuery varsa
        if (typeof $ !== 'undefined') {
            $(document).ajaxError((event, xhr, settings, error) => {
                this.handleAjaxError(xhr, settings, error);
            });
        }
        
        // Fetch interceptor
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            return originalFetch(...args).catch(error => {
                this.handleFetchError(error);
                throw error;
            });
        };
    }

    /**
     * Ajax hata işleme
     */
    handleAjaxError(xhr, settings, error) {
        console.error('[App] Ajax hatası:', error);
        
        if (xhr.status === 401) {
            this.handleUnauthorized();
        } else if (xhr.status === 403) {
            this.showToast('Bu işlem için yetkiniz yok', 'error');
        } else if (xhr.status === 500) {
            this.showToast('Sunucu hatası oluştu', 'error');
        } else if (xhr.status === 0) {
            this.showToast('Bağlantı hatası', 'error');
        }
    }

    /**
     * Fetch hata işleme
     */
    handleFetchError(error) {
        console.error('[App] Fetch hatası:', error);
        
        if (error.name === 'NetworkError') {
            this.showToast('Ağ bağlantısı hatası', 'error');
        }
    }

    /**
     * Yetkisiz erişim işleme
     */
    handleUnauthorized() {
        this.showToast('Oturumunuz sona erdi, yeniden giriş yapın', 'warning');
        
        setTimeout(() => {
            window.location.href = '/accounts/login/';
        }, 2000);
    }

    /**
     * Performance monitoring
     */
    setupPerformanceMonitoring() {
        // Performance observer
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.entryType === 'navigation') {
                        console.log(`[App] Page load time: ${entry.loadEventEnd - entry.loadEventStart}ms`);
                    }
                });
            });
            
            observer.observe({ entryTypes: ['navigation'] });
        }
        
        // Memory monitoring
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                if (memory.usedJSHeapSize > memory.jsHeapSizeLimit * 0.9) {
                    console.warn('[App] Memory kullanımı yüksek');
                }
            }, 60000); // 1 dakika
        }
    }

    /**
     * Offline veri sync
     */
    async syncOfflineData() {
        const offlineData = this.getOfflineData();
        
        if (offlineData.length > 0) {
            console.log(`[App] ${offlineData.length} offline veri sync ediliyor...`);
            
            for (const data of offlineData) {
                try {
                    await this.syncSingleData(data);
                    this.removeOfflineData(data.id);
                } catch (error) {
                    console.error('[App] Sync hatası:', error);
                }
            }
        }
    }

    /**
     * Periyodik görevleri duraklat
     */
    pausePeriodicTasks() {
        Object.values(this.modules).forEach(module => {
            if (module.pauseTasks) {
                module.pauseTasks();
            }
        });
    }

    /**
     * Periyodik görevleri devam ettir
     */
    resumePeriodicTasks() {
        Object.values(this.modules).forEach(module => {
            if (module.resumeTasks) {
                module.resumeTasks();
            }
        });
    }

    /**
     * Verileri yenile
     */
    refreshData() {
        Object.values(this.modules).forEach(module => {
            if (module.refresh) {
                module.refresh();
            }
        });
    }

    /**
     * Toast mesajı göster
     */
    showToast(message, type = 'info') {
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * Arama odaklama
     */
    focusSearch() {
        const searchInput = document.querySelector('#global-search');
        if (searchInput) {
            searchInput.focus();
        }
    }

    /**
     * Mevcut formu kaydet
     */
    saveCurrentForm() {
        const activeForm = document.querySelector('form:focus-within');
        if (activeForm) {
            const submitButton = activeForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.click();
            }
        }
    }

    /**
     * Modal'ları kapat
     */
    closeModals() {
        document.querySelectorAll('.modal:not(.hidden)').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    /**
     * Klavye kısayollarını göster
     */
    showKeyboardShortcuts() {
        const shortcuts = [
            'Ctrl+K: Arama',
            'Ctrl+S: Kaydet',
            'Ctrl+E: Dashboard',
            'Escape: Modal kapat'
        ];
        
        this.showToast(shortcuts.join('\n'), 'info');
    }

    /**
     * Utility methods
     */
    getOfflineData() {
        try {
            return JSON.parse(localStorage.getItem('offline_data') || '[]');
        } catch {
            return [];
        }
    }

    removeOfflineData(id) {
        const data = this.getOfflineData();
        const filtered = data.filter(item => item.id !== id);
        localStorage.setItem('offline_data', JSON.stringify(filtered));
    }

    saveUnsavedData() {
        // Form verilerini kaydet
        const forms = document.querySelectorAll('form[data-autosave]');
        forms.forEach(form => {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            localStorage.setItem(`autosave_${form.id}`, JSON.stringify(data));
        });
    }

    reportError(errorInfo) {
        // Hata raporlama servisi
        if (navigator.onLine) {
            fetch('/api/errors/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(errorInfo)
            }).catch(() => {
                // Sessiz başarısızlık
            });
        }
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

/**
 * Tema Yöneticisi Sınıfı
 * ======================
 * 
 * Karanlık/aydınlık mod geçişlerini yönetir.
 * Kullanıcı tercihlerini localStorage'da saklar.
 * Sistem teması ile entegre çalışır.
 */
class ThemeManager {
    constructor() {
        this.currentTheme = 'light';     // Varsayılan tema
        this.init();
    }

    /**
     * Tema yöneticisini başlat.
     * Kaydedilmiş tema tercihini uygula.
     */
    init() {
        this.applyStoredTheme();         // Kaydedilmiş temayı uygula
        this.setupThemeToggle();         // Tema değiştirme butonunu kur
    }

    /**
     * Kaydedilmiş tema tercihini uygula.
     * localStorage'dan tema bilgisini oku ve uygula.
     */
    applyStoredTheme() {
        const storedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Öncelik sırası: Kullanıcı tercihi > Sistem tercihi > Varsayılan
        if (storedTheme === 'dark' || (!storedTheme && systemPrefersDark)) {
            this.setTheme('dark');
        } else {
            this.setTheme('light');
        }
    }

    /**
     * Tema değiştirme butonunu kur.
     * Butona tıklanınca tema değişsin.
     */
    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    /**
     * Tema değiştirme işlemi.
     * Mevcut temanın tersine çevir.
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    /**
     * Belirtilen temayı uygula.
     * 
     * @param {string} theme - Tema adı ('light' veya 'dark')
     */
    setTheme(theme) {
        this.currentTheme = theme;
        
        // HTML element'ine class ekle/çıkar
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        
        // localStorage'a kaydet
        localStorage.setItem('theme', theme);
        
        // Tema butonunun görünümünü güncelle
        this.updateThemeToggleIcon(theme);
    }

    updateThemeToggleIcon(theme) {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }
}

/**
 * Form Yöneticisi Sınıfı
 * ======================
 * 
 * Form validasyonu, AJAX gönderimi ve otomatik kaydetme işlemlerini yönetir.
 * Kullanıcı deneyimini iyileştiren form özellikleri sağlar.
 */
class FormManager {
    constructor() {
        this.autoSaveInterval = 30000;   // 30 saniye
        this.init();
    }

    /**
     * Form yöneticisini başlat.
     */
    init() {
        this.setupFormValidation();      // Validasyon kurallarını kur
        this.setupFormSubmission();      // AJAX form gönderimi kur
        this.setupAutoSave();            // Otomatik kaydetmeyi kur
    }

    /**
     * Form validasyon kurallarını kur.
     * HTML5 validasyonu ile birlikte özel kurallar ekle.
     */
    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate="true"]');
        
        forms.forEach(form => {
            form.addEventListener('submit', (event) => {
                if (!this.validateForm(form)) {
                    event.preventDefault();  // Geçersizse gönderimi engelle
                }
            });
        });
    }

    /**
     * Form validasyonu yap.
     * 
     * @param {HTMLFormElement} form - Validate edilecek form
     * @returns {boolean} Geçerli ise true
     */
    validateForm(form) {
        let isValid = true;
        const fields = form.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            // HTML5 validasyonu
            if (!field.checkValidity()) {
                this.showFieldError(field, field.validationMessage);
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });
        
        return isValid;
    }

    /**
     * Alan hata mesajı göster.
     * 
     * @param {HTMLElement} field - Hatalı alan
     * @param {string} message - Hata mesajı
     */
    showFieldError(field, message) {
        // Hata sınıfı ekle
        field.classList.add('border-red-500', 'bg-red-50');
        
        // Hata mesajı elementi oluştur veya güncelle
        let errorElement = field.parentNode.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error text-red-500 text-sm mt-1';
            field.parentNode.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }

    /**
     * Alan hata mesajını temizle.
     * 
     * @param {HTMLElement} field - Temizlenecek alan
     */
    clearFieldError(field) {
        // Hata sınıflarını kaldır
        field.classList.remove('border-red-500', 'bg-red-50');
        
        // Hata mesajını kaldır
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    setupFormSubmission() {
        document.querySelectorAll('form[data-ajax]').forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitFormAjax(form);
            });
        });
    }

    async submitFormAjax(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        
        submitButton.disabled = true;
        submitButton.textContent = 'Gönderiliyor...';
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleFormSuccess(form, data);
            } else {
                this.handleFormError(form, response);
            }
        } catch (error) {
            this.handleFormError(form, error);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    }

    handleFormSuccess(form, data) {
        if (data.redirect) {
            window.location.href = data.redirect;
        } else {
            app.showToast(data.message || 'İşlem başarılı', 'success');
            form.reset();
        }
    }

    handleFormError(form, error) {
        app.showToast('Form gönderiminde hata oluştu', 'error');
    }

    setupAutoSave() {
        document.querySelectorAll('form[data-autosave]').forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    this.autoSaveForm(form);
                });
            });
        });
    }

    autoSaveForm(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        localStorage.setItem(`autosave_${form.id}`, JSON.stringify(data));
    }
}

/**
 * Modal Yöneticisi Sınıfı
 * =======================
 * 
 * Modal pencerelerinin açılma/kapanma işlemlerini yönetir.
 * Keyboard navigation ve accessibility desteği sağlar.
 */
class ModalManager {
    constructor() {
        this.activeModals = [];          // Aktif modal'lar
        this.init();
    }

    /**
     * Modal yöneticisini başlat.
     */
    init() {
        this.setupModalTriggers();       // Modal tetikleyicilerini kur
        this.setupModalClosing();        // Modal kapatma işlemlerini kur
    }

    /**
     * Modal tetikleyicilerini kur.
     * data-modal-target attribute'u olan butonlara event ekle.
     */
    setupModalTriggers() {
        const triggers = document.querySelectorAll('[data-modal-target]');
        
        triggers.forEach(trigger => {
            trigger.addEventListener('click', (event) => {
                event.preventDefault();
                const modalId = trigger.dataset.modalTarget;
                this.openModal(modalId);
            });
        });
    }

    /**
     * Modal kapatma işlemlerini kur.
     * Backdrop tıklama ve kapatma butonları.
     */
    setupModalClosing() {
        // Backdrop tıklama ile kapatma
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal-backdrop')) {
                this.closeModal(event.target.querySelector('.modal').id);
            }
        });
        
        // Kapatma butonları
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal-close')) {
                const modal = event.target.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            }
        });
        
        // ESC tuşu ile kapatma
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.activeModals.length > 0) {
                const lastModal = this.activeModals[this.activeModals.length - 1];
                this.closeModal(lastModal);
            }
        });
    }

    /**
     * Modal aç.
     * 
     * @param {string} modalId - Modal ID'si
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            this.activeModals.push(modalId);
            
            // Body scroll'unu engelle
            document.body.style.overflow = 'hidden';
        }
    }

    /**
     * Modal kapat.
     * 
     * @param {string} modalId - Modal ID'si
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            
            // Aktif modal listesinden çıkar
            this.activeModals = this.activeModals.filter(id => id !== modalId);
            
            // Başka modal yoksa body scroll'unu geri aç
            if (this.activeModals.length === 0) {
                document.body.style.overflow = '';
            }
        }
    }
}

/**
 * Arama Yöneticisi Sınıfı
 * =======================
 * 
 * Global arama işlemlerini yönetir.
 * Gerçek zamanlı arama ve sonuç gösterimi.
 */
class SearchManager {
    constructor() {
        this.searchInput = null;
        this.searchResults = null;
        this.searchTimeout = null;
        this.init();
    }

    /**
     * Arama yöneticisini başlat.
     */
    init() {
        this.setupSearchInput();         // Arama input'unu kur
    }

    /**
     * Arama input'unu kur.
     * Gerçek zamanlı arama için debounce uygula.
     */
    setupSearchInput() {
        this.searchInput = document.getElementById('global-search');
        this.searchResults = document.getElementById('search-results');
        
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (event) => {
                const query = event.target.value.trim();
                
                // Debounce - 300ms bekle
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    if (query.length >= 2) {
                        this.performSearch(query);
                    } else {
                        this.clearResults();
                    }
                }, 300);
            });
        }
    }

    /**
     * Arama işlemini gerçekleştir.
     * 
     * @param {string} query - Arama sorgusu
     */
    async performSearch(query) {
        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.displaySearchResults(data.results);
        } catch (error) {
            console.error('Arama hatası:', error);
        }
    }

    /**
     * Arama sonuçlarını göster.
     * 
     * @param {Array} results - Arama sonuçları
     */
    displaySearchResults(results) {
        if (!this.searchResults) return;
        
        if (results.length === 0) {
            this.searchResults.innerHTML = '<div class="p-4 text-gray-500">Sonuç bulunamadı</div>';
        } else {
            const resultsHTML = results.map(result => `
                <a href="${result.url}" class="block p-4 hover:bg-gray-100 border-b">
                    <div class="font-medium">${result.title}</div>
                    <div class="text-sm text-gray-600">${result.description}</div>
                    <div class="text-xs text-gray-400">${result.type}</div>
                </a>
            `).join('');
            
            this.searchResults.innerHTML = resultsHTML;
        }
        
        this.searchResults.classList.remove('hidden');
    }

    clearResults() {
        if (this.searchResults) {
            this.searchResults.classList.add('hidden');
            this.searchResults.innerHTML = '';
        }
    }
}

// Uygulama başlatma - DOM yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    // Global uygulama instance'ını oluştur
    window.Solutio360 = new Solutio360App();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Solutio360App;
} 