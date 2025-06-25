/**
 * Solutio 360 - Push Notification Manager
 * PWA için push bildirim yönetimi ve offline desteği
 */

class NotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
        this.permission = null;
        this.registration = null;
        this.endpoint = null;
        
        this.init();
    }
    
    /**
     * Notification sistemini başlatır
     */
    async init() {
        if (!this.isSupported) {
            console.warn('[NOTIFICATION] Tarayıcı bildirim desteği yok');
            return;
        }
        
        try {
            // Service Worker registration'ını al
            this.registration = await navigator.serviceWorker.ready;
            
            // Mevcut permission durumunu kontrol et
            this.permission = Notification.permission;
            
            console.log('[NOTIFICATION] Notification manager başlatıldı');
            
            // Mevcut subscription'ı kontrol et
            await this.checkExistingSubscription();
            
        } catch (error) {
            console.error('[NOTIFICATION] Başlatma hatası:', error);
        }
    }
    
    /**
     * Bildirim izni ister
     */
    async requestPermission() {
        if (!this.isSupported) {
            throw new Error('Bildirimler desteklenmiyor');
        }
        
        if (this.permission === 'granted') {
            return true;
        }
        
        try {
            this.permission = await Notification.requestPermission();
            
            if (this.permission === 'granted') {
                console.log('[NOTIFICATION] Bildirim izni verildi');
                
                // Push subscription oluştur
                await this.subscribeToPush();
                
                // Kullanıcıya teşekkür bildirimi gönder
                this.showWelcomeNotification();
                
                return true;
            } else {
                console.warn('[NOTIFICATION] Bildirim izni reddedildi');
                return false;
            }
        } catch (error) {
            console.error('[NOTIFICATION] İzin isteme hatası:', error);
            return false;
        }
    }
    
    /**
     * Push subscription oluşturur
     */
    async subscribeToPush() {
        if (!this.registration) {
            throw new Error('Service Worker kaydı bulunamadı');
        }
        
        try {
            // VAPID public key - production'da environment variable'dan al
            const vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa40HI6YplOFgD7qkjSAz8Q4G8BH8vT';
            
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey)
            });
            
            this.endpoint = subscription.endpoint;
            
            // Subscription'ı server'a gönder
            await this.sendSubscriptionToServer(subscription);
            
            console.log('[NOTIFICATION] Push subscription oluşturuldu');
            return subscription;
            
        } catch (error) {
            console.error('[NOTIFICATION] Push subscription hatası:', error);
            throw error;
        }
    }
    
    /**
     * Mevcut subscription'ı kontrol eder
     */
    async checkExistingSubscription() {
        if (!this.registration) return;
        
        try {
            const subscription = await this.registration.pushManager.getSubscription();
            
            if (subscription) {
                this.endpoint = subscription.endpoint;
                console.log('[NOTIFICATION] Mevcut subscription bulundu');
                
                // Server'a subscription durumunu bildir
                await this.sendSubscriptionToServer(subscription);
            }
        } catch (error) {
            console.error('[NOTIFICATION] Subscription kontrolü hatası:', error);
        }
    }
    
    /**
     * Subscription'ı server'a gönderir
     */
    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push-subscription/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON(),
                    user_agent: navigator.userAgent,
                    created_at: new Date().toISOString()
                })
            });
            
            if (!response.ok) {
                throw new Error('Subscription gönderme başarısız');
            }
            
            console.log('[NOTIFICATION] Subscription server\'a gönderildi');
        } catch (error) {
            console.error('[NOTIFICATION] Subscription gönderme hatası:', error);
        }
    }
    
    /**
     * Local bildirim gösterir
     */
    async showNotification(title, options = {}) {
        if (this.permission !== 'granted') {
            console.warn('[NOTIFICATION] Bildirim izni yok');
            return;
        }
        
        const defaultOptions = {
            body: '',
            icon: '/static/images/icons/icon-192x192.png',
            badge: '/static/images/icons/icon-72x72.png',
            tag: 'solutio360',
            requireInteraction: false,
            renotify: false,
            silent: false,
            timestamp: Date.now(),
            data: {
                url: '/',
                timestamp: new Date().toISOString()
            },
            actions: [
                {
                    action: 'open',
                    title: 'Aç',
                    icon: '/static/images/icons/icon-32x32.png'
                },
                {
                    action: 'close',
                    title: 'Kapat',
                    icon: '/static/images/icons/icon-32x32.png'
                }
            ]
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            if (this.registration) {
                // Service Worker üzerinden göster
                await this.registration.showNotification(title, finalOptions);
            } else {
                // Fallback: Browser notification
                new Notification(title, finalOptions);
            }
            
            console.log('[NOTIFICATION] Bildirim gösterildi:', title);
        } catch (error) {
            console.error('[NOTIFICATION] Bildirim gösterme hatası:', error);
        }
    }
    
    /**
     * Hoş geldiniz bildirimi
     */
    showWelcomeNotification() {
        this.showNotification('Solutio 360\'a Hoş Geldiniz! 🎉', {
            body: 'Bildirimler aktif edildi. Önemli güncellemelerden haberdar olacaksınız.',
            tag: 'welcome',
            requireInteraction: true,
            data: {
                url: '/dashboard/',
                type: 'welcome'
            }
        });
    }
    
    /**
     * Şikayet bildirimi
     */
    showComplaintNotification(complaint) {
        const title = 'Yeni Şikayet Oluşturuldu';
        const body = `${complaint.title}\nDurum: ${complaint.status}`;
        
        this.showNotification(title, {
            body: body,
            tag: `complaint-${complaint.id}`,
            data: {
                url: `/complaints/${complaint.id}/`,
                type: 'complaint',
                complaint_id: complaint.id
            }
        });
    }
    
    /**
     * Rapor bildirimi
     */
    showReportNotification(report) {
        const title = 'Rapor Hazır';
        const body = `${report.title} raporu oluşturuldu`;
        
        this.showNotification(title, {
            body: body,
            tag: `report-${report.id}`,
            data: {
                url: `/reports/${report.id}/`,
                type: 'report',
                report_id: report.id
            }
        });
    }
    
    /**
     * Sistem bildirimi
     */
    showSystemNotification(message, type = 'info') {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const title = `${icons[type]} Sistem Bildirimi`;
        
        this.showNotification(title, {
            body: message,
            tag: `system-${type}`,
            data: {
                url: '/dashboard/',
                type: 'system',
                level: type
            }
        });
    }
    
    /**
     * Offline sync bildirimi
     */
    showSyncNotification(syncedCount) {
        if (syncedCount > 0) {
            this.showNotification('Offline Veriler Senkronize Edildi', {
                body: `${syncedCount} adet offline işlem başarıyla senkronize edildi.`,
                tag: 'sync-success',
                data: {
                    url: '/dashboard/',
                    type: 'sync',
                    count: syncedCount
                }
            });
        }
    }
    
    /**
     * Subscription'ı iptal eder
     */
    async unsubscribe() {
        if (!this.registration) return;
        
        try {
            const subscription = await this.registration.pushManager.getSubscription();
            
            if (subscription) {
                await subscription.unsubscribe();
                
                // Server'a unsubscribe bildir
                await fetch('/api/push-unsubscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        endpoint: subscription.endpoint
                    })
                });
                
                this.endpoint = null;
                console.log('[NOTIFICATION] Push subscription iptal edildi');
            }
        } catch (error) {
            console.error('[NOTIFICATION] Unsubscribe hatası:', error);
        }
    }
    
    /**
     * Bildirim geçmişini temizler
     */
    async clearNotifications() {
        if (!this.registration) return;
        
        try {
            const notifications = await this.registration.getNotifications();
            
            for (const notification of notifications) {
                notification.close();
            }
            
            console.log('[NOTIFICATION] Tüm bildirimler temizlendi');
        } catch (error) {
            console.error('[NOTIFICATION] Bildirim temizleme hatası:', error);
        }
    }
    
    /**
     * Bildirim ayarlarını getirir
     */
    getSettings() {
        return {
            isSupported: this.isSupported,
            permission: this.permission,
            hasSubscription: !!this.endpoint,
            endpoint: this.endpoint
        };
    }
    
    /**
     * VAPID key'i byte array'e dönüştürür
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    /**
     * CSRF token'ı getirir
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Meta tag'den al
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
    
    /**
     * Test bildirimi gönderir
     */
    async sendTestNotification() {
        try {
            const response = await fetch('/api/test-notification/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                console.log('[NOTIFICATION] Test bildirimi gönderildi');
            }
        } catch (error) {
            console.error('[NOTIFICATION] Test bildirimi hatası:', error);
        }
    }
}

// Global instance
window.notificationManager = new NotificationManager();

// Sayfa yüklendiğinde bildirim durumunu kontrol et
document.addEventListener('DOMContentLoaded', () => {
    // Bildirim izni durumunu UI'da göster
    updateNotificationUI();
});

/**
 * Bildirim UI'sını günceller
 */
function updateNotificationUI() {
    const notificationButton = document.getElementById('notification-toggle');
    if (!notificationButton) return;
    
    const settings = window.notificationManager.getSettings();
    
    if (!settings.isSupported) {
        notificationButton.disabled = true;
        notificationButton.textContent = 'Desteklenmiyor';
        return;
    }
    
    switch (settings.permission) {
        case 'granted':
            notificationButton.textContent = 'Bildirimler Aktif';
            notificationButton.classList.add('active');
            break;
        case 'denied':
            notificationButton.textContent = 'Bildirimler Reddedildi';
            notificationButton.disabled = true;
            break;
        default:
            notificationButton.textContent = 'Bildirimleri Aktifleştir';
            notificationButton.classList.remove('active');
    }
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}

console.log('[NOTIFICATION] Notification manager yüklendi'); 