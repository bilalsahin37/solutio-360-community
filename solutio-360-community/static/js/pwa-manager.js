/**
 * Solutio 360 - PWA Yönetim Sistemi
 * =================================
 * 
 * Progressive Web App özelliklerini yöneten JavaScript kütüphanesi.
 * Çevrimdışı çalışma, bildirimler, uygulama yükleme ve senkronizasyon.
 * 
 * PWA Özellikleri:
 * - Service Worker kaydı ve yönetimi
 * - Uygulama yükleme prompt'ı
 * - Push bildirimleri
 * - Çevrimdışı veri senkronizasyonu
 * - Network durumu takibi
 * - Cache yönetimi
 * 
 * @author Solutio 360 Development Team
 * @version 1.0.0
 */

class PWAManager {
    /**
     * PWA Manager yapıcısı.
     * PWA özelliklerini yönetmek için gerekli değişkenleri başlatır.
     */
    constructor() {
        this.deferredPrompt = null;           // Install prompt referansı
        this.isInstalled = false;             // Uygulama yüklü mü kontrolü
        this.syncQueue = [];                  // Çevrimdışı senkronizasyon kuyruğu
        this.notificationPermission = 'default';  // Bildirim izni durumu
        
        this.init();  // Başlatma metodunu çağır
    }

    /**
     * PWA Manager'ı başlatır.
     * Tüm PWA özelliklerini kurar ve etkinleştirir.
     */
    async init() {
        console.log('[PWA] PWA Manager başlatılıyor...');
        
        // Service Worker'ı kaydet - çevrimdışı işlevsellik için
        await this.registerServiceWorker();
        
        // Install prompt dinleyicisi - uygulama yükleme için
        this.setupInstallPrompt();
        
        // Notification permission kontrolü - bildirimler için
        await this.checkNotificationPermission();
        
        // Network status dinleyicisi - çevrimiçi/çevrimdışı durumu
        this.setupNetworkListener();
        
        // Background sync setup - çevrimdışı veri senkronizasyonu
        this.setupBackgroundSync();
        
        console.log('[PWA] PWA Manager başlatıldı');
    }

    /**
     * Service Worker'ı kaydeder.
     * Çevrimdışı işlevsellik ve cache yönetimi için gerekli.
     * 
     * @returns {Promise<ServiceWorkerRegistration>} Service Worker kaydı
     */
    async registerServiceWorker() {
        // Service Worker desteği kontrolü
        if ('serviceWorker' in navigator) {
            try {
                // Service Worker dosyasını kaydet
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('[PWA] Service Worker kaydedildi:', registration.scope);
                
                // Güncelleme kontrolü - yeni sürüm mevcut mu?
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        // Yeni worker yüklendi ve mevcut worker var
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();  // Güncelleme bildirimi göster
                        }
                    });
                });
                
                return registration;
            } catch (error) {
                console.error('[PWA] Service Worker kaydı başarısız:', error);
            }
        }
    }

    /**
     * Uygulama yükleme prompt'ı ayarlarını yapar.
     * Kullanıcıya uygulamayı ana ekrana ekleme seçeneği sunar.
     */
    setupInstallPrompt() {
        // Tarayıcı install prompt'ını yakala
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt yakalandı');
            e.preventDefault();  // Varsayılan prompt'ı engelle
            this.deferredPrompt = e;  // Prompt'ı sakla
            
            // Daha önce dismiss edilmemişse banner göster
            if (!localStorage.getItem('pwa-install-dismissed')) {
                this.showInstallBanner();
            }
        });

        // Uygulama yüklendikten sonra
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] Uygulama yüklendi');
            this.isInstalled = true;
            this.hideInstallBanner();  // Banner'ı gizle
            this.showToast('Uygulama başarıyla yüklendi!', 'success');
        });
    }

    /**
     * Uygulama yükleme banner'ını gösterir.
     * Kullanıcıya uygulamayı yükleme seçeneği sunar.
     */
    showInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.remove('hidden');  // Banner'ı görünür yap
            
            // Install button click handler
            const installBtn = document.getElementById('pwa-install-btn');
            const dismissBtn = document.getElementById('pwa-dismiss-btn');
            
            if (installBtn) {
                installBtn.addEventListener('click', () => this.promptInstall());
            }
            
            if (dismissBtn) {
                dismissBtn.addEventListener('click', () => this.dismissInstallBanner());
            }
        }
    }

    /**
     * Install banner'ını gizler.
     */
    hideInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.add('hidden');
        }
    }

    /**
     * Uygulama yükleme prompt'ını tetikler.
     * Kullanıcıya uygulama yükleme dialog'unu gösterir.
     */
    async promptInstall() {
        if (this.deferredPrompt) {
            // Install prompt'ını göster
            this.deferredPrompt.prompt();
            
            // Kullanıcının seçimini bekle
            const { outcome } = await this.deferredPrompt.userChoice;
            console.log('[PWA] Install prompt sonucu:', outcome);
            
            // Prompt'ı temizle
            this.deferredPrompt = null;
            this.hideInstallBanner();
            
            if (outcome === 'accepted') {
                this.showToast('Uygulama yükleniyor...', 'info');
            }
        }
    }

    /**
     * Install banner'ını dismiss eder.
     * 7 gün boyunca tekrar gösterilmez.
     */
    dismissInstallBanner() {
        this.hideInstallBanner();
        localStorage.setItem('pwa-install-dismissed', 'true');
        
        // 7 gün sonra tekrar göster
        setTimeout(() => {
            localStorage.removeItem('pwa-install-dismissed');
        }, 7 * 24 * 60 * 60 * 1000);  // 7 gün = 7 * 24 * 60 * 60 * 1000 ms
    }

    /**
     * Bildirim iznini kontrol eder.
     * Gerekirse kullanıcıdan izin ister.
     */
    async checkNotificationPermission() {
        // Notification API desteği kontrolü
        if ('Notification' in window) {
            this.notificationPermission = Notification.permission;
            
            // Henüz izin verilmemişse
            if (this.notificationPermission === 'default') {
                // 5 saniye sonra izin iste (kullanıcı deneyimi için)
                setTimeout(() => {
                    this.requestNotificationPermission();
                }, 5000);
            }
        }
    }

    /**
     * Bildirim izni ister.
     * Kullanıcıdan push bildirim gönderme izni alır.
     */
    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            // İzin iste
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            
            if (permission === 'granted') {
                this.showToast('Bildirimler etkinleştirildi!', 'success');
            }
        }
    }

    /**
     * Push notification gönderir.
     * Service Worker aracılığıyla bildirim gösterir.
     * 
     * @param {string} title - Bildirim başlığı
     * @param {Object} options - Bildirim seçenekleri
     */
    showNotification(title, options = {}) {
        // Bildirim izni kontrolü
        if (this.notificationPermission === 'granted') {
            // Varsayılan bildirim seçenekleri
            const defaultOptions = {
                icon: '/static/images/icons/icon-192x192.png',    // Bildirim ikonu
                badge: '/static/images/icons/icon-72x72.png',     // Badge ikonu
                vibrate: [200, 100, 200],                        // Titreşim deseni
                data: {
                    timestamp: Date.now()  // Zaman damgası
                }
            };
            
            // Seçenekleri birleştir
            const finalOptions = { ...defaultOptions, ...options };
            
            // Service Worker aracılığıyla bildirim gönder
            if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                navigator.serviceWorker.controller.postMessage({
                    type: 'SHOW_NOTIFICATION',
                    title: title,
                    options: finalOptions
                });
            } else {
                // Fallback: Doğrudan bildirim
                new Notification(title, finalOptions);
            }
        }
    }

    /**
     * Network durumunu dinle
     */
    setupNetworkListener() {
        window.addEventListener('online', () => {
            console.log('[PWA] Çevrimiçi duruma geçildi');
            this.showToast('İnternet bağlantısı yeniden kuruldu', 'success');
            this.processSyncQueue();
        });

        window.addEventListener('offline', () => {
            console.log('[PWA] Çevrimdışı duruma geçildi');
            this.showToast('İnternet bağlantısı kesildi. Offline modda çalışıyorsunuz.', 'warning');
        });
    }

    /**
     * Background sync ayarları
     */
    setupBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            console.log('[PWA] Background Sync destekleniyor');
        }
    }

    /**
     * Sync kuyruğuna veri ekle
     */
    addToSyncQueue(data) {
        this.syncQueue.push({
            id: Date.now(),
            data: data,
            timestamp: new Date().toISOString()
        });
        
        localStorage.setItem('pwa-sync-queue', JSON.stringify(this.syncQueue));
        
        if (navigator.onLine) {
            this.processSyncQueue();
        }
    }

    /**
     * Sync kuyruğunu işle
     */
    async processSyncQueue() {
        const queue = JSON.parse(localStorage.getItem('pwa-sync-queue') || '[]');
        
        if (queue.length === 0) return;
        
        console.log('[PWA] Sync kuyruğu işleniyor...', queue.length, 'öğe');
        
        for (const item of queue) {
            try {
                await this.syncData(item.data);
                this.removeSyncItem(item.id);
            } catch (error) {
                console.error('[PWA] Sync hatası:', error);
            }
        }
    }

    /**
     * Veriyi sync et
     */
    async syncData(data) {
        const response = await fetch('/api/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Sync başarısız');
        }
        
        return response.json();
    }

    /**
     * Sync öğesini kaldır
     */
    removeSyncItem(id) {
        this.syncQueue = this.syncQueue.filter(item => item.id !== id);
        localStorage.setItem('pwa-sync-queue', JSON.stringify(this.syncQueue));
    }

    /**
     * CSRF token al
     */
    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    /**
     * Update notification göster
     */
    showUpdateNotification() {
        this.showToast('Uygulama güncellendi! Yeniden yükleyin.', 'info');
        
        // 5 saniye sonra otomatik yenile seçeneği
        setTimeout(() => {
            if (confirm('Uygulamayı şimdi yeniden yüklemek ister misiniz?')) {
                window.location.reload();
            }
        }, 5000);
    }

    /**
     * Toast mesajı göster
     */
    showToast(message, type = 'info') {
        // Base.html'deki showToast fonksiyonunu kullan
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            console.log(`[PWA] ${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Cache temizle
     */
    async clearCache() {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(
                cacheNames.map(cacheName => caches.delete(cacheName))
            );
            console.log('[PWA] Cache temizlendi');
        }
    }

    /**
     * Offline veri kaydet
     */
    saveOfflineData(key, data) {
        try {
            localStorage.setItem(`offline-${key}`, JSON.stringify({
                data: data,
                timestamp: Date.now()
            }));
        } catch (error) {
            console.error('[PWA] Offline veri kaydetme hatası:', error);
        }
    }

    /**
     * Offline veri al
     */
    getOfflineData(key, maxAge = 24 * 60 * 60 * 1000) { // 24 saat
        try {
            const stored = localStorage.getItem(`offline-${key}`);
            if (!stored) return null;
            
            const { data, timestamp } = JSON.parse(stored);
            
            if (Date.now() - timestamp > maxAge) {
                localStorage.removeItem(`offline-${key}`);
                return null;
            }
            
            return data;
        } catch (error) {
            console.error('[PWA] Offline veri alma hatası:', error);
            return null;
        }
    }
}

// PWA Manager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    window.pwaManager = new PWAManager();
});

// Global erişim için
window.PWAManager = PWAManager; 