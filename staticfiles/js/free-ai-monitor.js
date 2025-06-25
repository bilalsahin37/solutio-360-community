/**
 * 🆓 FREE AI Provider Monitor
 * Real-time monitoring and auto-switching of free AI providers
 * Zero-cost AI system management
 */

class FreeAIMonitor {
    constructor() {
        this.providers = {
            'local': { name: 'Local Models', limit: 'unlimited', icon: '🏠' },
            'huggingface': { name: 'Hugging Face', limit: 1000, icon: '🤗' },
            'gemini': { name: 'Gemini Free', limit: 15, icon: '💎' },
            'anthropic': { name: 'Claude Free', limit: 5, icon: '🤖' },
            'openai': { name: 'OpenAI (DISABLED)', limit: 0, icon: '❌' }
        };
        
        this.updateInterval = 30000; // 30 seconds
        this.statusContainer = null;
        
        this.initializeWidget();
        this.startMonitoring();
    }
    
    initializeWidget() {
        // Create status widget HTML
        const widget = document.createElement('div');
        widget.className = 'free-ai-status-widget';
        widget.innerHTML = `
            <div class="ai-status-header">
                <h4>🆓 FREE AI Status</h4>
                <span class="cost-badge">$0.00 Today</span>
            </div>
            <div class="ai-providers-list" id="ai-providers-list">
                <div class="loading">Loading AI status...</div>
            </div>
            <div class="ai-tips">
                <button class="btn-tips" onclick="aiMonitor.showTips()">💡 Optimization Tips</button>
                <button class="btn-test" onclick="aiMonitor.testProviders()">🧪 Test All</button>
            </div>
        `;
        
        // Add to dashboard
        const dashboard = document.querySelector('.dashboard-widgets') || document.body;
        dashboard.appendChild(widget);
        
        this.statusContainer = document.getElementById('ai-providers-list');
    }
    
    async fetchAIStatus() {
        try {
            const response = await fetch('/api/ai/api/ai-status/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateStatusWidget(data);
                return data;
            }
        } catch (error) {
            console.error('AI Status fetch error:', error);
            this.showError('Failed to fetch AI status');
        }
    }
    
    updateStatusWidget(data) {
        if (!this.statusContainer) return;
        
        let html = '';
        
        for (const [providerKey, providerInfo] of Object.entries(data.providers)) {
            const config = this.providers[providerKey] || { name: providerKey, icon: '🤖' };
            const status = providerInfo.status;
            const isAvailable = status.includes('Available');
            
            html += `
                <div class="provider-item ${isAvailable ? 'available' : 'exhausted'}">
                    <div class="provider-header">
                        <span class="provider-icon">${config.icon}</span>
                        <span class="provider-name">${config.name}</span>
                        <span class="provider-status">${status}</span>
                    </div>
                    <div class="provider-details">
                        <div class="usage-info">
                            <span>Used: ${providerInfo.used}</span>
                            <span>Limit: ${providerInfo.limit}</span>
                            <span>Remaining: ${providerInfo.remaining}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${providerInfo.percentage}%"></div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.statusContainer.innerHTML = html;
    }
    
    async switchProvider(taskType = 'sentiment_analysis') {
        try {
            const response = await fetch('/api/ai/api/ai-switch/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    task_type: taskType,
                    current_provider: 'local'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showNotification(`🔄 Switched to ${data.to} for ${taskType}`, 'success');
                return data;
            }
        } catch (error) {
            console.error('Provider switch error:', error);
            this.showError('Failed to switch provider');
        }
    }
    
    async showTips() {
        try {
            const response = await fetch('/api/ai/api/ai-tips/');
            const data = await response.json();
            
            if (data.success) {
                this.showModal('💡 AI Optimization Tips', `
                    <div class="ai-tips-modal">
                        <h3>🆓 ${data.strategy}</h3>
                        <div class="tips-list">
                            ${data.tips.map(tip => `<div class="tip-item">${tip}</div>`).join('')}
                        </div>
                        <h4>📊 Daily Limits:</h4>
                        <ul class="limits-list">
                            ${Object.entries(data.daily_limits).map(([provider, limit]) => 
                                `<li><strong>${provider}:</strong> ${limit}</li>`
                            ).join('')}
                        </ul>
                        <h4>🚀 Recommended Workflow:</h4>
                        <ol class="workflow-list">
                            ${data.recommended_workflow.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                `);
            }
        } catch (error) {
            console.error('Tips fetch error:', error);
        }
    }
    
    async testProviders() {
        const providers = ['local', 'huggingface', 'gemini', 'anthropic'];
        const testText = 'Bu harika bir test mesajıdır! Pozitif sentiment analizi için idealdir.';
        
        this.showNotification('🧪 Testing all providers...', 'info');
        
        for (const provider of providers) {
            try {
                const response = await fetch('/api/ai/api/ai-test/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        provider: provider,
                        text: testText
                    })
                });
                
                const data = await response.json();
                const icon = this.providers[provider]?.icon || '🤖';
                
                if (data.success) {
                    this.showNotification(`${icon} ${provider}: ✅ Success (${data.test_result.cost})`, 'success');
                } else {
                    this.showNotification(`${icon} ${provider}: ❌ ${data.error}`, 'error');
                }
                
                // Delay between tests
                await new Promise(resolve => setTimeout(resolve, 1000));
                
            } catch (error) {
                console.error(`Test error for ${provider}:`, error);
            }
        }
    }
    
    startMonitoring() {
        // Initial fetch
        this.fetchAIStatus();
        
        // Regular updates
        setInterval(() => {
            this.fetchAIStatus();
        }, this.updateInterval);
        
        console.log('🆓 Free AI Monitor started - Zero cost AI system active!');
    }
    
    showModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'ai-modal-overlay';
        modal.innerHTML = `
            <div class="ai-modal">
                <div class="ai-modal-header">
                    <h3>${title}</h3>
                    <button class="ai-modal-close" onclick="this.closest('.ai-modal-overlay').remove()">×</button>
                </div>
                <div class="ai-modal-content">
                    ${content}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `ai-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                ${message}
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    showError(message) {
        this.showNotification(`❌ ${message}`, 'error');
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.aiMonitor = new FreeAIMonitor();
});

// Export for manual initialization
window.FreeAIMonitor = FreeAIMonitor; 