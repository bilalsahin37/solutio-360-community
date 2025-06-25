
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.installModal = document.getElementById('pwa-install-modal');
        this.installButton = document.getElementById('pwa-install-btn');
        this.closeButton = document.getElementById('pwa-install-close');
        
        this.init();
    }
    
    init() {
        // Kurulum olayını dinle
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallModal();
        });
        
        // Kurulum butonuna tıklama
        this.installButton?.addEventListener('click', () => this.installPWA());
        
        // Kapatma butonuna tıklama
        this.closeButton?.addEventListener('click', () => this.hideInstallModal());
        
        // PWA durumunu kontrol et
        this.checkPWAStatus();
    }
    
    // PWA Kurulum modalını göster
    showInstallModal() {
        if (this.installModal && !this.isPWAInstalled()) {
            this.installModal.style.display = 'flex';
        }
    }
    
    // PWA Kurulum modalını gizle
    hideInstallModal() {
        if (this.installModal) {
            this.installModal.style.display = 'none';
        }
    }
    
    // PWA'yı kur
    async installPWA() {
        if (!this.deferredPrompt) return;
        
        try {
            // Kurulum promptunu göster
            const result = await this.deferredPrompt.prompt();
            console.log('PWA kurulum sonucu:', result);
            
            // Prompt'u temizle
            this.deferredPrompt = null;
            
            // Modalı gizle
            this.hideInstallModal();
            
            // Kurulum başarılıysa
            if (result.outcome === 'accepted') {
                this.showInstallSuccess();
            }
        } catch (error) {
            console.error('PWA kurulum hatası:', error);
            this.showInstallError();
        }
    }
    
    // PWA kurulu mu kontrol et
    isPWAInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }
    
    // PWA durumunu kontrol et
    checkPWAStatus() {
        if ('serviceWorker' in navigator) {
            // Service Worker'ı kaydet
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then(registration => {
                    console.log('Service Worker başarıyla kaydedildi:', registration);
                    
                    // Periyodik senkronizasyonu etkinleştir
                    if ('periodicSync' in registration) {
                        registration.periodicSync.register('sync-offline-requests', {
                            minInterval: 60 * 60 * 1000 // 1 saat
                        });
                    }
                })
                .catch(error => {
                    console.error('Service Worker kaydı başarısız:', error);
                });
        }
    }
    
    // Kurulum başarılı mesajı
    showInstallSuccess() {
        const notification = document.createElement('div');
        notification.className = 'pwa-notification success';
        notification.textContent = 'Uygulama başarıyla kuruldu!';
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
    
    // Kurulum hata mesajı
    showInstallError() {
        const notification = document.createElement('div');
        notification.className = 'pwa-notification error';
        notification.textContent = 'Uygulama kurulumu başarısız oldu. Lütfen tekrar deneyin.';
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
}

// PWA yöneticisini başlat
window.addEventListener('load', () => {
    new PWAManager();
}); 