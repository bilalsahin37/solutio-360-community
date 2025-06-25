/**
 * Solutio 360 - Dashboard Management
 * Dashboard sayfası için özel JavaScript işlevselliği
 */

class DashboardManager {
    constructor() {
        this.refreshInterval = 30000; // 30 saniye
        this.charts = {};
        this.widgets = {};
        this.notifications = [];
        
        this.init();
    }

    /**
     * Dashboard Manager'ı başlat
     */
    init() {
        console.log('[Dashboard] Dashboard Manager başlatılıyor...');
        
        // Event listener'ları ayarla
        this.setupEventListeners();
        
        // Bildirim sistemi
        this.initNotifications();
        
        // Real-time güncellemeler
        this.setupRealTimeUpdates();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        console.log('[Dashboard] Dashboard Manager başlatıldı');
    }

    /**
     * Event listener'ları ayarla
     */
    setupEventListeners() {
        // Refresh butonları
        document.querySelectorAll('[data-action="refresh"]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.refreshWidget(button.dataset.target);
            });
        });

        // Quick actions
        document.querySelectorAll('[data-action="quick-action"]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleQuickAction(button.dataset.action, button.dataset.target);
            });
        });

        // Search functionality
        const searchInput = document.querySelector('#global-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performGlobalSearch(e.target.value);
                }, 300);
            });
        }

        // Widget controls
        document.querySelectorAll('[data-widget-control]').forEach(control => {
            control.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleWidgetControl(control);
            });
        });
    }

    /**
     * Bildirim sistemini başlat
     */
    initNotifications() {
        // Bildirimleri yükle
        this.loadNotifications();
        
        // Periyodik bildirim kontrolü
        setInterval(() => {
            this.loadNotifications();
        }, 60000); // 1 dakika

        // Bildirim dropdown toggle
        const notificationToggle = document.querySelector('#notification-toggle');
        const notificationDropdown = document.querySelector('#notification-dropdown');
        
        if (notificationToggle && notificationDropdown) {
            notificationToggle.addEventListener('click', (e) => {
                e.preventDefault();
                notificationDropdown.classList.toggle('hidden');
            });
            
            // Dışarı tıklamada kapat
            document.addEventListener('click', (e) => {
                if (!notificationToggle.contains(e.target) && !notificationDropdown.contains(e.target)) {
                    notificationDropdown.classList.add('hidden');
                }
            });
        }
    }

    /**
     * Bildirimleri yükle
     */
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateNotificationUI(data.notifications, data.unread_count);
            }
        } catch (error) {
            console.error('[Dashboard] Bildirim yükleme hatası:', error);
        }
    }

    /**
     * Bildirim UI'ını güncelle
     */
    updateNotificationUI(notifications, unreadCount) {
        // Unread count badge
        const badge = document.querySelector('#notification-badge');
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }

        // Notification list
        const notificationList = document.querySelector('#notification-list');
        if (notificationList) {
            notificationList.innerHTML = '';
            
            if (notifications.length === 0) {
                notificationList.innerHTML = `
                    <div class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                        Yeni bildirim yok
                    </div>
                `;
            } else {
                notifications.forEach(notification => {
                    const notificationElement = this.createNotificationElement(notification);
                    notificationList.appendChild(notificationElement);
                });
            }
        }
    }

    /**
     * Bildirim elementi oluştur
     */
    createNotificationElement(notification) {
        const div = document.createElement('div');
        div.className = 'px-4 py-3 border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer';
        div.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <div class="w-2 h-2 mt-2 bg-blue-500 rounded-full"></div>
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm text-gray-900 dark:text-white">${notification.message}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        ${this.formatNotificationTime(notification.created_at)}
                    </p>
                </div>
            </div>
        `;
        
        div.addEventListener('click', () => {
            this.markNotificationAsRead(notification.id);
            if (notification.url) {
                window.location.href = notification.url;
            }
        });
        
        return div;
    }

    /**
     * Bildirim zamanını formatla
     */
    formatNotificationTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'Az önce';
        if (diff < 3600) return `${Math.floor(diff / 60)} dakika önce`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} saat önce`;
        return date.toLocaleDateString('tr-TR');
    }

    /**
     * Bildirimi okundu olarak işaretle
     */
    async markNotificationAsRead(notificationId) {
        try {
            await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            // Bildirimleri yeniden yükle
            this.loadNotifications();
        } catch (error) {
            console.error('[Dashboard] Bildirim okuma hatası:', error);
        }
    }

    /**
     * Real-time güncellemeler
     */
    setupRealTimeUpdates() {
        // Periyodik veri güncellemesi
        setInterval(() => {
            this.refreshDashboardData();
        }, this.refreshInterval);
        
        // Page visibility API ile optimize et
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshDashboardData();
            }
        });
    }

    /**
     * Dashboard verilerini yenile
     */
    async refreshDashboardData() {
        try {
            const response = await fetch('/api/dashboard/stats/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
            }
        } catch (error) {
            console.error('[Dashboard] Veri yenileme hatası:', error);
        }
    }

    /**
     * Dashboard istatistiklerini güncelle
     */
    updateDashboardStats(data) {
        // İstatistik kartlarını güncelle
        Object.keys(data).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = data[key];
                
                // Animasyon efekti
                element.classList.add('animate-pulse');
                setTimeout(() => {
                    element.classList.remove('animate-pulse');
                }, 1000);
            }
        });
    }

    /**
     * Widget'ı yenile
     */
    async refreshWidget(widgetId) {
        const widget = document.querySelector(`#${widgetId}`);
        if (!widget) return;
        
        const refreshButton = widget.querySelector('[data-action="refresh"]');
        if (refreshButton) {
            refreshButton.classList.add('animate-spin');
        }
        
        try {
            const response = await fetch(`/api/widgets/${widgetId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateWidget(widgetId, data);
            }
        } catch (error) {
            console.error('[Dashboard] Widget yenileme hatası:', error);
        } finally {
            if (refreshButton) {
                refreshButton.classList.remove('animate-spin');
            }
        }
    }

    /**
     * Widget'ı güncelle
     */
    updateWidget(widgetId, data) {
        const widget = document.querySelector(`#${widgetId}`);
        if (!widget) return;
        
        const content = widget.querySelector('.widget-content');
        if (content && data.html) {
            content.innerHTML = data.html;
        }
        
        // Timestamp güncelle
        const timestamp = widget.querySelector('.widget-timestamp');
        if (timestamp) {
            timestamp.textContent = `Son güncelleme: ${new Date().toLocaleTimeString('tr-TR')}`;
        }
    }

    /**
     * Quick action'ı işle
     */
    handleQuickAction(action, target) {
        switch (action) {
            case 'new-complaint':
                window.location.href = '/complaints/create/';
                break;
            case 'view-reports':
                window.location.href = '/reports/';
                break;
            case 'export-data':
                this.exportDashboardData(target);
                break;
            case 'refresh-all':
                this.refreshAllWidgets();
                break;
            default:
                console.warn('[Dashboard] Bilinmeyen quick action:', action);
        }
    }

    /**
     * Widget kontrolünü işle
     */
    handleWidgetControl(control) {
        const action = control.dataset.widgetControl;
        const widgetId = control.closest('[id]').id;
        
        switch (action) {
            case 'minimize':
                this.minimizeWidget(widgetId);
                break;
            case 'maximize':
                this.maximizeWidget(widgetId);
                break;
            case 'configure':
                this.configureWidget(widgetId);
                break;
            case 'remove':
                this.removeWidget(widgetId);
                break;
        }
    }

    /**
     * Global arama
     */
    async performGlobalSearch(query) {
        if (query.length < 2) {
            this.hideSearchResults();
            return;
        }
        
        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.showSearchResults(data.results);
            }
        } catch (error) {
            console.error('[Dashboard] Arama hatası:', error);
        }
    }

    /**
     * Arama sonuçlarını göster
     */
    showSearchResults(results) {
        let searchResults = document.querySelector('#search-results');
        
        if (!searchResults) {
            searchResults = document.createElement('div');
            searchResults.id = 'search-results';
            searchResults.className = 'absolute top-full left-0 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-b-lg shadow-lg z-50';
            
            const searchContainer = document.querySelector('#global-search').parentElement;
            searchContainer.style.position = 'relative';
            searchContainer.appendChild(searchResults);
        }
        
        if (results.length === 0) {
            searchResults.innerHTML = `
                <div class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    Sonuç bulunamadı
                </div>
            `;
        } else {
            searchResults.innerHTML = results.map(result => `
                <a href="${result.url}" class="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                    <div class="flex items-center">
                        <span class="text-xs bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-2 py-1 rounded mr-3">
                            ${result.type}
                        </span>
                        <div>
                            <div class="text-sm font-medium text-gray-900 dark:text-white">${result.title}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">${result.description}</div>
                        </div>
                    </div>
                </a>
            `).join('');
        }
    }

    /**
     * Arama sonuçlarını gizle
     */
    hideSearchResults() {
        const searchResults = document.querySelector('#search-results');
        if (searchResults) {
            searchResults.remove();
        }
    }

    /**
     * Keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'k':
                        e.preventDefault();
                        document.querySelector('#global-search')?.focus();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshAllWidgets();
                        break;
                    case 'n':
                        e.preventDefault();
                        window.location.href = '/complaints/create/';
                        break;
                }
            }
        });
    }

    /**
     * Tüm widget'ları yenile
     */
    refreshAllWidgets() {
        document.querySelectorAll('[data-widget]').forEach(widget => {
            this.refreshWidget(widget.id);
        });
    }

    /**
     * Dashboard verilerini export et
     */
    async exportDashboardData(format = 'pdf') {
        try {
            const response = await fetch(`/api/dashboard/export/?format=${format}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `dashboard-${new Date().toISOString().split('T')[0]}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            }
        } catch (error) {
            console.error('[Dashboard] Export hatası:', error);
        }
    }

    /**
     * CSRF token al
     */
    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    /**
     * Widget minimize
     */
    minimizeWidget(widgetId) {
        const widget = document.querySelector(`#${widgetId}`);
        const content = widget.querySelector('.widget-content');
        if (content) {
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Widget maximize
     */
    maximizeWidget(widgetId) {
        const widget = document.querySelector(`#${widgetId}`);
        widget.classList.toggle('col-span-full');
    }

    /**
     * Widget konfigürasyonu
     */
    configureWidget(widgetId) {
        // Widget konfigürasyon modalı açılacak
        console.log('Widget konfigürasyonu:', widgetId);
    }

    /**
     * Widget kaldır
     */
    removeWidget(widgetId) {
        if (confirm('Bu widget\'ı kaldırmak istediğinize emin misiniz?')) {
            const widget = document.querySelector(`#${widgetId}`);
            if (widget) {
                widget.remove();
            }
        }
    }
}

// Dashboard Manager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});

// Global erişim için
window.DashboardManager = DashboardManager; 