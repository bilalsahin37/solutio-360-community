/**
 * Solutio 360 - Analytics ve Raporlama Modülü
 * ==========================================
 * 
 * Şikayet ve rapor verilerinin analiz edilmesi için JavaScript kütüphanesi.
 * Chart.js kullanarak dinamik grafikler ve istatistikler oluşturur.
 * 
 * Özellikler:
 * - Line, Bar, Pie chart desteği
 * - Gerçek zamanlı veri güncelleme
 * - Widget tabanlı yapı
 * - PDF/Excel dışa aktarma
 * - Otomatik yenileme
 * 
 * @author Solutio 360 Development Team
 * @version 1.0.0
 */

class AnalyticsManager {
    /**
     * Analytics Manager yapıcısı.
     * Grafik ve widget yönetimi için temel değişkenleri ayarlar.
     */
    constructor() {
        this.charts = {};              // Oluşturulan Chart.js grafikleri
        this.widgets = {};             // Widget referansları
        this.refreshInterval = 30000;  // Otomatik yenileme süresi (30 saniye)
        this.init();                   // Başlatma metodunu çağır
    }

    /**
     * Analytics Manager'ı başlatır.
     * Tüm grafikleri, widget'ları ve otomatik yenileme sistemini kurar.
     */
    init() {
        console.log('[Analytics] Analytics Manager başlatılıyor...');
        
        // Chart.js konfigürasyonu - varsayılan ayarları belirle
        this.setupChartDefaults();
        
        // Widget'ları başlat - DOM'daki tüm grafik elementlerini bul ve oluştur
        this.initializeWidgets();
        
        // Otomatik refresh ayarla - belirli aralıklarla veri güncelle
        this.setupAutoRefresh();
        
        console.log('[Analytics] Analytics Manager başlatıldı');
    }

    /**
     * Chart.js varsayılan ayarlarını yapılandırır.
     * Tüm grafikler için ortak stil ve davranış ayarları.
     */
    setupChartDefaults() {
        if (typeof Chart !== 'undefined') {
            // Font ailesi - modern web fontları
            Chart.defaults.font.family = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            
            // Varsayılan metin rengi - koyu gri
            Chart.defaults.color = '#6B7280';
            
            // Legend'ı varsayılan olarak gizle
            Chart.defaults.plugins.legend.display = false;
            
            // Responsive tasarım aktif
            Chart.defaults.responsive = true;
            
            // Aspect ratio'yu koruma
            Chart.defaults.maintainAspectRatio = false;
        }
    }

    /**
     * Sayfadaki tüm widget'ları bulur ve başlatır.
     * data-widget attribute'una göre widget türlerini belirler.
     */
    initializeWidgets() {
        // Chart widget'larını bul ve oluştur
        document.querySelectorAll('[data-widget="chart"]').forEach(element => {
            this.createChart(element);
        });

        // Metrik widget'larını başlat (sayı göstergeleri)
        document.querySelectorAll('[data-widget="metric"]').forEach(element => {
            this.createMetric(element);
        });

        // Tablo widget'larını başlat
        document.querySelectorAll('[data-widget="table"]').forEach(element => {
            this.createTable(element);
        });
    }

    /**
     * Chart widget oluşturur.
     * Element'in data attribute'larından yapılandırma alır.
     * 
     * @param {HTMLElement} element - Chart container elementi
     */
    createChart(element) {
        // Chart türünü al (varsayılan: line)
        const chartType = element.dataset.chartType || 'line';
        
        // Veri kaynağı URL'si
        const dataSource = element.dataset.dataSource;
        
        // Unique chart ID
        const chartId = element.id;

        // Veri kaynağı kontrolü
        if (!dataSource) {
            console.error('[Analytics] Chart için veri kaynağı belirtilmemiş:', chartId);
            return;
        }

        // Veriyi yükle ve chart oluştur
        this.loadData(dataSource)
            .then(data => {
                // Canvas elementini bul
                const canvas = element.querySelector('canvas');
                if (!canvas) {
                    console.error('[Analytics] Canvas elementi bulunamadı:', chartId);
                    return;
                }

                // Chart.js ile grafik oluştur
                const ctx = canvas.getContext('2d');
                const chart = new Chart(ctx, this.getChartConfig(chartType, data));
                
                // Chart'ı kaydet (sonradan güncelleme için)
                this.charts[chartId] = chart;
                console.log('[Analytics] Chart oluşturuldu:', chartId);
            })
            .catch(error => {
                console.error('[Analytics] Chart veri yükleme hatası:', error);
                this.showError(element, 'Veri yüklenirken hata oluştu');
            });
    }

    /**
     * Chart türüne göre Chart.js konfigürasyonu döndürür.
     * 
     * @param {string} type - Chart türü (line, bar, pie)
     * @param {Object} data - Chart verisi
     * @returns {Object} Chart.js konfigürasyonu
     */
    getChartConfig(type, data) {
        // Tüm chart türleri için ortak ayarlar
        const baseConfig = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',  // Tooltip arka plan
                    titleColor: '#fff',                      // Tooltip başlık rengi
                    bodyColor: '#fff',                       // Tooltip metin rengi
                    borderColor: '#374151',                  // Tooltip kenarlık
                    borderWidth: 1
                }
            }
        };

        switch (type) {
            case 'line':
                // Line chart - zaman serisi verileri için ideal
                return {
                    type: 'line',
                    data: {
                        labels: data.labels,    // X ekseni etiketleri
                        datasets: [{
                            label: data.label || 'Veri',
                            data: data.values,  // Y ekseni değerleri
                            borderColor: '#3B82F6',              // Çizgi rengi (mavi)
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',  // Alan rengi
                            tension: 0.4,       // Çizgi yumuşaklığı
                            fill: true          // Alanı doldur
                        }]
                    },
                    options: {
                        ...baseConfig,
                        scales: {
                            y: {
                                beginAtZero: true,  // Y ekseni sıfırdan başlasın
                                grid: {
                                    color: 'rgba(156, 163, 175, 0.3)'  // Grid çizgi rengi
                                }
                            },
                            x: {
                                grid: {
                                    color: 'rgba(156, 163, 175, 0.3)'
                                }
                            }
                        }
                    }
                };

            case 'bar':
                // Bar chart - kategorik veriler için ideal
                return {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: data.label || 'Veri',
                            data: data.values,
                            // Çok renkli bar'lar için renk paleti
                            backgroundColor: [
                                '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
                                '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'
                            ].slice(0, data.values.length)
                        }]
                    },
                    options: {
                        ...baseConfig,
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(156, 163, 175, 0.3)'
                                }
                            },
                            x: {
                                grid: {
                                    display: false  // X ekseni grid'ini gizle
                                }
                            }
                        }
                    }
                };

            case 'pie':
                // Pie chart - oransal veriler için ideal
                return {
                    type: 'pie',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.values,
                            // Pie dilimler için renk paleti
                            backgroundColor: [
                                '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
                                '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'
                            ]
                        }]
                    },
                    options: {
                        ...baseConfig,
                        plugins: {
                            ...baseConfig.plugins,
                            legend: {
                                display: true,     // Pie chart'ta legend göster
                                position: 'bottom' // Legend pozisyonu
                            }
                        }
                    }
                };

            default:
                // Bilinmeyen chart türü için line chart döndür
                return this.getChartConfig('line', data);
        }
    }

    /**
     * Metrik widget oluştur
     */
    createMetric(element) {
        const dataSource = element.dataset.dataSource;
        const metricId = element.id;

        if (!dataSource) {
            console.error('[Analytics] Metrik için veri kaynağı belirtilmemiş:', metricId);
            return;
        }

        this.loadData(dataSource)
            .then(data => {
                this.updateMetric(element, data);
                this.widgets[metricId] = { type: 'metric', element, data };
                console.log('[Analytics] Metrik oluşturuldu:', metricId);
            })
            .catch(error => {
                console.error('[Analytics] Metrik veri yükleme hatası:', error);
                this.showError(element, 'Veri yüklenirken hata oluştu');
            });
    }

    /**
     * Metriği güncelle
     */
    updateMetric(element, data) {
        const valueElement = element.querySelector('[data-metric="value"]');
        const changeElement = element.querySelector('[data-metric="change"]');
        const labelElement = element.querySelector('[data-metric="label"]');

        if (valueElement) {
            valueElement.textContent = this.formatNumber(data.value);
        }

        if (changeElement && data.change !== undefined) {
            const change = data.change;
            const isPositive = change >= 0;
            
            changeElement.textContent = `${isPositive ? '+' : ''}${change}%`;
            changeElement.className = `text-sm font-medium ${
                isPositive ? 'text-green-600' : 'text-red-600'
            }`;
        }

        if (labelElement && data.label) {
            labelElement.textContent = data.label;
        }
    }

    /**
     * Tablo widget oluştur
     */
    createTable(element) {
        const dataSource = element.dataset.dataSource;
        const tableId = element.id;

        if (!dataSource) {
            console.error('[Analytics] Tablo için veri kaynağı belirtilmemiş:', tableId);
            return;
        }

        this.loadData(dataSource)
            .then(data => {
                this.updateTable(element, data);
                this.widgets[tableId] = { type: 'table', element, data };
                console.log('[Analytics] Tablo oluşturuldu:', tableId);
            })
            .catch(error => {
                console.error('[Analytics] Tablo veri yükleme hatası:', error);
                this.showError(element, 'Veri yüklenirken hata oluştu');
            });
    }

    /**
     * Tabloyu güncelle
     */
    updateTable(element, data) {
        const tbody = element.querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        data.rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50 dark:hover:bg-gray-700/50';

            row.forEach(cell => {
                const td = document.createElement('td');
                td.className = 'px-4 py-3 text-sm text-gray-900 dark:text-white';
                td.textContent = cell;
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });
    }

    /**
     * Veri yükle
     */
    async loadData(dataSource) {
        const response = await fetch(`/api/analytics/${dataSource}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCSRFToken()
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * CSRF token al
     */
    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    /**
     * Sayıyı formatla
     */
    formatNumber(number) {
        if (number >= 1000000) {
            return (number / 1000000).toFixed(1) + 'M';
        } else if (number >= 1000) {
            return (number / 1000).toFixed(1) + 'K';
        }
        return number.toString();
    }

    /**
     * Hata göster
     */
    showError(element, message) {
        element.innerHTML = `
            <div class="flex items-center justify-center h-32 text-red-500">
                <div class="text-center">
                    <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <p class="text-sm">${message}</p>
                </div>
            </div>
        `;
    }

    /**
     * Otomatik refresh ayarla
     */
    setupAutoRefresh() {
        setInterval(() => {
            this.refreshAll();
        }, this.refreshInterval);
    }

    /**
     * Tüm widget'ları yenile
     */
    async refreshAll() {
        console.log('[Analytics] Widget\'lar yenileniyor...');

        // Chart'ları yenile
        for (const [chartId, chart] of Object.entries(this.charts)) {
            await this.refreshChart(chartId, chart);
        }

        // Diğer widget'ları yenile
        for (const [widgetId, widget] of Object.entries(this.widgets)) {
            await this.refreshWidget(widgetId, widget);
        }
    }

    /**
     * Chart'ı yenile
     */
    async refreshChart(chartId, chart) {
        try {
            const element = document.getElementById(chartId);
            const dataSource = element.dataset.dataSource;
            
            const data = await this.loadData(dataSource);
            
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.values;
            chart.update('none');
            
        } catch (error) {
            console.error('[Analytics] Chart yenileme hatası:', chartId, error);
        }
    }

    /**
     * Widget'ı yenile
     */
    async refreshWidget(widgetId, widget) {
        try {
            const dataSource = widget.element.dataset.dataSource;
            const data = await this.loadData(dataSource);
            
            if (widget.type === 'metric') {
                this.updateMetric(widget.element, data);
            } else if (widget.type === 'table') {
                this.updateTable(widget.element, data);
            }
            
        } catch (error) {
            console.error('[Analytics] Widget yenileme hatası:', widgetId, error);
        }
    }

    /**
     * Export işlevleri
     */
    exportChart(chartId, format = 'png') {
        const chart = this.charts[chartId];
        if (!chart) {
            console.error('[Analytics] Chart bulunamadı:', chartId);
            return;
        }

        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `chart-${chartId}.${format}`;
        link.href = url;
        link.click();
    }

    /**
     * Rapor oluştur
     */
    async generateReport(config) {
        try {
            const response = await fetch('/api/reports/generate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(config)
            });

            if (!response.ok) {
                throw new Error('Rapor oluşturulamadı');
            }

            const result = await response.json();
            
            if (result.download_url) {
                window.open(result.download_url, '_blank');
            }

            return result;

        } catch (error) {
            console.error('[Analytics] Rapor oluşturma hatası:', error);
            throw error;
        }
    }
}

// Analytics Manager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    window.analyticsManager = new AnalyticsManager();
});

// Global erişim için
window.AnalyticsManager = AnalyticsManager; 