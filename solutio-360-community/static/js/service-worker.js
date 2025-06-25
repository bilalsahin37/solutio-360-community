// PWA Yapılandırma
const PWA_CONFIG = {
    appName: 'Solutio 360',
    shortName: 'Solutio360',
    description: 'Modern, modüler ve offline çalışabilen şikayet yönetim sistemi.',
    themeColor: '#2563eb',
    backgroundColor: '#181c20',
    display: 'standalone',
    scope: '/',
    startUrl: '/',
    icons: [
        { src: '/static/images/icons/icon-72x72.png', sizes: '72x72', type: 'image/png' },
        { src: '/static/images/icons/icon-96x96.png', sizes: '96x96', type: 'image/png' },
        { src: '/static/images/icons/icon-128x128.png', sizes: '128x128', type: 'image/png' },
        { src: '/static/images/icons/icon-144x144.png', sizes: '144x144', type: 'image/png' },
        { src: '/static/images/icons/icon-152x152.png', sizes: '152x152', type: 'image/png' },
        { src: '/static/images/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
        { src: '/static/images/icons/icon-384x384.png', sizes: '384x384', type: 'image/png' },
        { src: '/static/images/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' }
    ],
    cacheFiles: [
        '/',
        '/static/css/output.css',
        '/static/css/style.css',
        '/static/js/main.js',
        '/static/js/pwa-install.js',
        '/static/js/particles.min.js',
        '/static/js/service-worker.js',
        '/static/images/favicon.png',
        '/static/fonts/inter-var.woff2',
        '/api/v1/complaints/',
        '/api/v1/reports/',
    ]
};

const DB_CONFIG = {
    name: 'solutio360-db',
    version: 1,
    stores: {
        complaints: { keyPath: 'id', autoIncrement: true },
        reports: { keyPath: 'id', autoIncrement: true },
        offlineRequests: { keyPath: 'id', autoIncrement: true }
    }
};

const CACHE_NAME = 'solutio360-cache-v1';
const OFFLINE_PAGE = '/offline.html';

// Service Worker Kurulumu
self.addEventListener('install', event => {
  event.waitUntil(
        Promise.all([
            // Temel cache'leme
            caches.open(CACHE_NAME).then(cache => {
                return cache.addAll(PWA_CONFIG.cacheFiles);
            }),
            // Offline sayfasını cache'le
            caches.open(CACHE_NAME).then(cache => {
                return cache.add(OFFLINE_PAGE);
            })
        ])
  );
});

// Service Worker Aktivasyonu
self.addEventListener('activate', event => {
  event.waitUntil(
        Promise.all([
            // Eski cache'leri temizle
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
            )),
            // IndexedDB veritabanını oluştur
            createDatabase()
        ])
  );
});

// Fetch İsteklerini Yakala
self.addEventListener('fetch', event => {
    // API istekleri için özel strateji
    if (event.request.url.includes('/api/')) {
        handleApiRequest(event);
    }
    // Statik dosyalar için cache-first stratejisi
    else if (event.request.method === 'GET') {
    event.respondWith(
            caches.match(event.request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetchAndCache(event.request);
                })
                .catch(() => {
                    // Offline sayfa göster
                    return caches.match(OFFLINE_PAGE);
      })
    );
  }
});

// API İsteklerini İşle
function handleApiRequest(event) {
    if (event.request.method === 'GET') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clonedResponse = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => cache.put(event.request, clonedResponse));
                    return response;
                })
                .catch(() => {
                    return caches.match(event.request);
                })
        );
    } else {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return saveOfflineRequest(event.request);
                })
        );
    }
}

// Offline İstekleri Kaydet
async function saveOfflineRequest(request) {
    const db = await openDB();
    const tx = db.transaction('offlineRequests', 'readwrite');
    const store = tx.objectStore('offlineRequests');
    
    const serializedRequest = {
        url: request.url,
        method: request.method,
        headers: Array.from(request.headers.entries()),
        body: await request.clone().text(),
        timestamp: Date.now()
    };
    
    await store.add(serializedRequest);
    
    return new Response(JSON.stringify({
        success: false,
        offline: true,
        message: 'İstek offline olarak kaydedildi ve internet bağlantısı sağlandığında gönderilecek.'
    }), {
        headers: { 'Content-Type': 'application/json' }
    });
}

// IndexedDB Veritabanını Oluştur
function createDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_CONFIG.name, DB_CONFIG.version);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Store'ları oluştur
            Object.entries(DB_CONFIG.stores).forEach(([storeName, config]) => {
                if (!db.objectStoreNames.contains(storeName)) {
                    db.createObjectStore(storeName, config);
                }
            });
    };
  });
}

// IndexedDB'yi Aç
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_CONFIG.name, DB_CONFIG.version);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

// Fetch ve Cache
async function fetchAndCache(request) {
    try {
        const response = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        return caches.match(OFFLINE_PAGE);
    }
}

// Periyodik Senkronizasyon
self.addEventListener('periodicsync', event => {
    if (event.tag === 'sync-offline-requests') {
        event.waitUntil(syncOfflineRequests());
    }
});

// Offline İstekleri Senkronize Et
async function syncOfflineRequests() {
    const db = await openDB();
    const tx = db.transaction('offlineRequests', 'readwrite');
    const store = tx.objectStore('offlineRequests');
    const requests = await store.getAll();
    
    for (const request of requests) {
        try {
            await fetch(request.url, {
                method: request.method,
                headers: new Headers(request.headers),
                body: request.body
            });
            await store.delete(request.id);
        } catch (error) {
            console.error('Senkronizasyon hatası:', error);
        }
    }
} 