/**
 * Solutio 360 - Service Worker
 * PWA için cache stratejileri ve offline desteği
 */

const CACHE_NAME = 'solutio-360-v1.0.0';
const STATIC_CACHE = 'solutio-static-v1.0.0';
const DYNAMIC_CACHE = 'solutio-dynamic-v1.0.0';

// Cache edilecek statik dosyalar
const STATIC_ASSETS = [
    '/',
    '/static/css/output.css',
    '/static/js/main.js',
    '/static/js/jquery.min.js',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-512x512.png',
    '/static/manifest.json',
    '/offline/',
    '/accounts/login/',
    '/dashboard/'
];

// Cache edilmeyecek URL'ler
const EXCLUDE_URLS = [
    '/admin/',
    '/api/',
    '/accounts/logout/',
    '/static/admin/',
    '/media/',
    '/__debug__/'
];

// Service Worker kurulumu
self.addEventListener('install', event => {
    console.log('[SW] Service Worker yükleniyor...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE).then(cache => {
            console.log('[SW] Statik dosyalar cache ediliyor...');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    
    // Yeni SW'yi hemen aktifleştir
    self.skipWaiting();
});

// Service Worker aktivasyonu
self.addEventListener('activate', event => {
    console.log('[SW] Service Worker aktifleştiriliyor...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    // Eski cache'leri temizle
                    if (cacheName !== STATIC_CACHE && 
                        cacheName !== DYNAMIC_CACHE &&
                        cacheName !== CACHE_NAME) {
                        console.log('[SW] Eski cache siliniyor:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Tüm istemcileri kontrol al
    self.clients.claim();
});

// Fetch olayları - Network-First stratejisi
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // Hariç tutulan URL'leri atla
    if (EXCLUDE_URLS.some(excludeUrl => url.pathname.startsWith(excludeUrl))) {
        return;
    }
    
    // POST, PUT, DELETE istekleri için network-only
    if (event.request.method !== 'GET') {
        event.respondWith(fetch(event.request));
        return;
    }
    
    // Statik dosyalar için Cache-First
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirst(event.request));
        return;
    }
    
    // Diğer istekler için Network-First
    event.respondWith(networkFirst(event.request));
});

// Cache-First stratejisi (statik dosyalar için)
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            console.log('[SW] Cache\'den sunuluyor:', request.url);
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        console.error('[SW] Cache-First hatası:', error);
        return caches.match('/offline/');
    }
}

// Network-First stratejisi (dinamik içerik için)
async function networkFirst(request) {
    try {
        // Önce network'ten dene
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Başarılı ise cache'e kaydet
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
        
    } catch (error) {
        console.log('[SW] Network başarısız, cache\'den deneniyor:', request.url);
        
        // Network başarısız ise cache'den dene
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Hiçbiri yoksa offline sayfası
        if (request.destination === 'document') {
            return caches.match('/offline/');
        }
        
        return new Response('İçerik offline mevcut değil', {
            status: 404,
            statusText: 'Not Found'
        });
    }
}

// Background Sync desteği
self.addEventListener('sync', event => {
    console.log('[SW] Background sync tetiklendi:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(syncData());
    }
});

// Offline verilerini sync etme
async function syncData() {
    try {
        // IndexedDB'den bekleyen verileri al ve gönder
        console.log('[SW] Offline veriler sync ediliyor...');
        
        // Bu kısım IndexedDB entegrasyonu ile genişletilebilir
        const response = await fetch('/api/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            console.log('[SW] Sync başarılı');
        }
        
    } catch (error) {
        console.error('[SW] Sync hatası:', error);
    }
}

// Push bildirimleri
self.addEventListener('push', event => {
    console.log('[SW] Push bildirimi alındı');
    
    let notificationData = {
        title: 'Solutio 360',
        body: 'Yeni bildiriminiz var',
        icon: '/static/images/icons/icon-192x192.png',
        badge: '/static/images/icons/icon-72x72.png',
        data: {
            url: '/'
        }
    };
    
    if (event.data) {
        const data = event.data.json();
        notificationData = { ...notificationData, ...data };
    }
    
    event.waitUntil(
        self.registration.showNotification(notificationData.title, {
            body: notificationData.body,
            icon: notificationData.icon,
            badge: notificationData.badge,
            data: notificationData.data,
            requireInteraction: true,
            actions: [
                {
                    action: 'open',
                    title: 'Aç'
                },
                {
                    action: 'close',
                    title: 'Kapat'
                }
            ]
        })
    );
});

// Bildirim tıklama olayları
self.addEventListener('notificationclick', event => {
    console.log('[SW] Bildirime tıklandı:', event.action);
    
    event.notification.close();
    
    if (event.action === 'open' || !event.action) {
        const url = event.notification.data?.url || '/';
        
        event.waitUntil(
            clients.openWindow(url)
        );
    }
});

console.log('[SW] Service Worker yüklendi - Solutio 360 PWA'); 