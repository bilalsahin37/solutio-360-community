/**
 * PWA Main Entry Point
 * Progressive Web App ana giriş noktası
 */

// PWA durumu global değişkenleri
window.PWA = {
    isInstalled: false,
    isOnline: navigator.onLine,
    serviceWorker: null,
    installPrompt: null
};

/**
 * PWA'yı başlat
 */
document.addEventListener('DOMContentLoaded', function() {
    initPWA();
});

/**
 * PWA başlatma işlemleri
 */
async function initPWA() {
    console.log('🚀 PWA başlatılıyor...');
    
    try {
        // Service Worker'ı kaydet
        await registerServiceWorker();
        
        // Install prompt'u hazırla
        setupInstallPrompt();
        
        // Network durumunu izle
        setupNetworkMonitoring();
        
        console.log('✅ PWA başarıyla başlatıldı');
        
    } catch (error) {
        console.error('❌ PWA başlatma hatası:', error);
    }
}

/**
 * Service Worker kaydı
 */
async function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.register('/static/js/sw.js', {
                scope: '/'
            });
            
            window.PWA.serviceWorker = registration;
            console.log('✅ Service Worker kaydedildi:', registration.scope);
            
        } catch (error) {
            console.error('❌ Service Worker kayıt hatası:', error);
        }
    } else {
        console.warn('⚠️ Service Worker desteklenmiyor');
    }
}

/**
 * Uygulama yükleme prompt'unu hazırla
 */
function setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        window.PWA.installPrompt = e;
        showInstallBanner();
        console.log('📱 PWA yükleme prompt'u hazır');
    });
    
    window.addEventListener('appinstalled', () => {
        window.PWA.isInstalled = true;
        hideInstallBanner();
        console.log('🎉 PWA başarıyla yüklendi');
    });
}

/**
 * Network durumunu izle
 */
function setupNetworkMonitoring() {
    window.addEventListener('online', () => {
        window.PWA.isOnline = true;
        hideOfflineBanner();
        console.log('🌐 İnternet bağlantısı geri geldi');
    });
    
    window.addEventListener('offline', () => {
        window.PWA.isOnline = false;
        showOfflineBanner();
        console.log('📡 İnternet bağlantısı kesildi');
    });
}

/**
 * Install banner'ını göster
 */
function showInstallBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.classList.remove('hidden');
    }
}

/**
 * Install banner'ını gizle
 */
function hideInstallBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.classList.add('hidden');
    }
}

/**
 * Offline banner'ını göster
 */
function showOfflineBanner() {
    let banner = document.getElementById('offline-banner');
    
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.className = 'fixed top-0 left-0 right-0 bg-red-600 text-white text-center py-2 z-50';
        banner.textContent = 'İnternet bağlantısı yok - Offline modda çalışıyorsunuz';
        document.body.appendChild(banner);
    }
    
    banner.classList.remove('hidden');
}

/**
 * Offline banner'ını gizle
 */
function hideOfflineBanner() {
    const banner = document.getElementById('offline-banner');
    if (banner) {
        banner.classList.add('hidden');
    }
}

/**
 * PWA yükleme işlemini başlat
 */
async function installPWA() {
    if (!window.PWA.installPrompt) {
        console.log('Install prompt mevcut değil');
        return false;
    }
    
    try {
        window.PWA.installPrompt.prompt();
        
        const { outcome } = await window.PWA.installPrompt.userChoice;
        
        if (outcome === 'accepted') {
            console.log('✅ Kullanıcı PWA yüklemeyi kabul etti');
        } else {
            console.log('❌ Kullanıcı PWA yüklemeyi reddetti');
        }
        
        window.PWA.installPrompt = null;
        hideInstallBanner();
        
        return outcome === 'accepted';
        
    } catch (error) {
        console.error('PWA yükleme hatası:', error);
        return false;
    }
}

// Global fonksiyonları export et
window.installPWA = installPWA;

// Event handler'lar için global tanımlamalar
window.addEventListener('load', () => {
    const installButton = document.getElementById('pwa-install-btn');
    if (installButton) {
        installButton.addEventListener('click', installPWA);
    }
});

console.log('�� PWA.js yüklendi'); 
