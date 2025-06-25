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
        {
            src: '/static/images/icons/icon-72x72.png',
            sizes: '72x72',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-96x96.png',
            sizes: '96x96',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-128x128.png',
            sizes: '128x128',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-144x144.png',
            sizes: '144x144',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-152x152.png',
            sizes: '152x152',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-384x384.png',
            sizes: '384x384',
            type: 'image/png'
        },
        {
            src: '/static/images/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
        }
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
        // Font dosyaları
        '/static/fonts/inter-var.woff2',
        // Temel API endpoint'leri
        '/api/v1/complaints/',
        '/api/v1/reports/',
    ]
};

// IndexedDB yapılandırması
const DB_CONFIG = {
    name: 'solutio360-db',
    version: 1,
    stores: {
        complaints: { keyPath: 'id', autoIncrement: true },
        reports: { keyPath: 'id', autoIncrement: true },
        offlineRequests: { keyPath: 'id', autoIncrement: true }
    }
};

export { DB_CONFIG, PWA_CONFIG };
