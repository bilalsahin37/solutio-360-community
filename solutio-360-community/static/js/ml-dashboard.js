/**
 * ML Dashboard JavaScript
 * Makine Öğrenmesi Dashboard için ana JavaScript dosyası
 */

class MLDashboard {
    constructor() {
        this.charts = {};
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.init();
    }

    init() {
        console.log('[ML Dashboard] Başlatılıyor...');
        this.setupWebSocket();
        this.initializeCharts();
        this.setupEventListeners();
        this.startPeriodicUpdates();
        this.animateMetrics();
    }

    setupWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${wsProtocol}://${window.location.host}/ws/ml-dashboard/`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('[ML Dashboard] WebSocket bağlandı');
                this.reconnectAttempts = 0;
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.socket.onclose = () => {
                console.log('[ML Dashboard] WebSocket kapandı');
                this.attemptReconnection();
            };
            
        } catch (error) {
            console.error('[ML Dashboard] WebSocket hatası:', error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'ml_metrics_update':
                this.updateMLMetrics(data.payload);
                break;
            case 'anomaly_detected':
                this.handleAnomalyAlert(data.payload);
                break;
            case 'prediction_update':
                this.updatePredictions(data.payload);
                break;
        }
    }

    attemptReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                this.setupWebSocket();
            }, 3000 * this.reconnectAttempts);
        }
    }

    initializeCharts() {
        this.initVolumeChart();
        this.initSentimentChart();
        this.initAnomalyPlot();
        this.initRLChart();
        this.initCategoryChart();
    }

    initVolumeChart() {
        const canvas = document.getElementById('volume-prediction-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.volumePrediction = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateDateLabels(7),
                datasets: [{
                    label: 'Tahmini Şikayet Sayısı',
                    data: [],
                    borderColor: '#4299e1',
                    backgroundColor: 'rgba(66, 153, 225, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }

    initSentimentChart() {
        const canvas = document.getElementById('sentiment-trend-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.sentimentTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateDateLabels(30),
                datasets: [{
                    label: 'Pozitif',
                    data: [],
                    borderColor: '#48bb78',
                    tension: 0.4
                }, {
                    label: 'Negatif',
                    data: [],
                    borderColor: '#f56565',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }

    initAnomalyPlot() {
        const plotDiv = document.getElementById('anomaly-detection-plot');
        if (!plotDiv) return;

        const trace1 = {
            x: [], y: [], mode: 'markers', type: 'scatter',
            name: 'Normal', marker: { color: '#48bb78', size: 8 }
        };

        const trace2 = {
            x: [], y: [], mode: 'markers', type: 'scatter',
            name: 'Anomali', marker: { color: '#f56565', size: 12 }
        };

        const layout = {
            title: 'Anomali Tespiti',
            showlegend: false,
            margin: { t: 50, l: 50, r: 50, b: 50 }
        };

        Plotly.newPlot(plotDiv, [trace1, trace2], layout, { responsive: true });
        this.charts.anomalyPlot = plotDiv;
    }

    initRLChart() {
        const canvas = document.getElementById('rl-rewards-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.rlRewards = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Kümülatif Ödül',
                    data: [],
                    borderColor: '#9f7aea',
                    backgroundColor: 'rgba(159, 122, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }

    initCategoryChart() {
        const canvas = document.getElementById('category-prediction-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.charts.categoryPrediction = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: ['#4299e1', '#48bb78', '#ed8936', '#f56565', '#9f7aea']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%'
            }
        });
    }

    setupEventListeners() {
        // Refresh ve export butonları için event listener'lar
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="refresh-models"]')) {
                e.preventDefault();
                this.refreshAllModels();
            }
            if (e.target.matches('[data-action="export-insights"]')) {
                e.preventDefault();
                this.exportInsights();
            }
        });
    }

    startPeriodicUpdates() {
        setInterval(() => {
            this.fetchLatestData();
        }, 30000);
    }

    animateMetrics() {
        document.querySelectorAll('.bar-fill').forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = width;
            }, 100);
        });
    }

    updateMLMetrics(data) {
        this.updateStatusCards(data);
        this.updateCharts(data);
    }

    updateStatusCards(data) {
        if (data.anomaly_score !== undefined) {
            const element = document.getElementById('anomaly-score');
            if (element) element.textContent = data.anomaly_score.toFixed(2);
        }
        
        if (data.avg_sentiment !== undefined) {
            const element = document.getElementById('avg-sentiment');
            if (element) element.textContent = data.avg_sentiment.toFixed(2);
        }
    }

    updateCharts(data) {
        if (data.volume_predictions && this.charts.volumePrediction) {
            this.charts.volumePrediction.data.datasets[0].data = data.volume_predictions;
            this.charts.volumePrediction.update('none');
        }
        
        if (data.sentiment_trends && this.charts.sentimentTrend) {
            this.charts.sentimentTrend.data.datasets[0].data = data.sentiment_trends.positive;
            this.charts.sentimentTrend.data.datasets[1].data = data.sentiment_trends.negative;
            this.charts.sentimentTrend.update('none');
        }
    }

    handleAnomalyAlert(data) {
        console.log('Anomali tespit edildi:', data);
        this.showNotification('Anomali Tespit Edildi!', data.message, 'warning');
    }

    async refreshAllModels() {
        try {
            const response = await fetch('/api/ml/refresh-models/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateMLMetrics(data);
                this.showNotification('Başarı', 'Modeller yenilendi', 'success');
            }
        } catch (error) {
            console.error('Model yenileme hatası:', error);
        }
    }

    async exportInsights() {
        try {
            const response = await fetch('/api/ml/export-insights/');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ml-insights-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Export hatası:', error);
        }
    }

    async fetchLatestData() {
        try {
            const response = await fetch('/api/ml/dashboard-data/');
            if (response.ok) {
                const data = await response.json();
                this.updateMLMetrics(data);
            }
        } catch (error) {
            console.error('Veri getirme hatası:', error);
        }
    }

    showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <strong>${title}</strong>
                <p>${message}</p>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
        
        notification.querySelector('.notification-close').onclick = () => notification.remove();
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    generateDateLabels(days) {
        const labels = [];
        const today = new Date();
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('tr-TR', { 
                month: 'short', 
                day: 'numeric' 
            }));
        }
        
        return labels;
    }
}

// Global fonksiyonlar
let mlDashboard = null;

function initializeMLDashboard() {
    if (!mlDashboard) {
        mlDashboard = new MLDashboard();
    }
}

function refreshAllModels() {
    if (mlDashboard) mlDashboard.refreshAllModels();
}

function exportInsights() {
    if (mlDashboard) mlDashboard.exportInsights();
}

function updateMLMetrics(data) {
    if (mlDashboard) mlDashboard.updateMLMetrics(data);
}

// Sayfa yüklendiğinde başlat
document.addEventListener('DOMContentLoaded', initializeMLDashboard); 