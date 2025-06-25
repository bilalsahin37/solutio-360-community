/**
 * Enterprise AI Chatbot Integration
 * LeewayHertz-style intelligent customer service chatbot
 * CDN-free implementation with Turkish language support
 */

class AICustomerServiceChatbot {
    constructor(options = {}) {
        this.apiEndpoint = options.apiEndpoint || '/analytics/api/process-complaint-ai/';
        this.autoResponseEndpoint = options.autoResponseEndpoint || '/analytics/api/auto-response/';
        this.sentimentEndpoint = options.sentimentEndpoint || '/analytics/api/sentiment-analysis/';
        
        this.isInitialized = false;
        this.isTyping = false;
        this.conversationHistory = [];
        this.currentSessionId = this.generateSessionId();
        
        // UI Elements
        this.chatContainer = null;
        this.messagesContainer = null;
        this.userInput = null;
        this.sendButton = null;
        this.toggleButton = null;
        
        // AI Features
        this.enableSentimentAnalysis = true;
        this.enableAutoRouting = true;
        this.enableMultiLanguage = true;
        this.enableCulturalContext = true;
        
        // Predefined responses for common queries
        this.quickResponses = {
            'tr': {
                'greeting': [
                    'Merhaba! Size nasıl yardımcı olabilirim?',
                    'Solutio 360 AI asistanına hoş geldiniz! Sorularınızı yanıtlamak için buradayım.',
                    'Merhaba! Şikayetiniz veya sorunuzla ilgili size yardımcı olmaktan mutluluk duyarım.'
                ],
                'technical_help': [
                    'Teknik konularda size yardımcı olabilirim. Sorunun detaylarını paylaşır mısınız?',
                    'Teknik destek için doğru yerdesiniz. Probleminizi açıklayın, çözüm bulalım.',
                    'Sistem sorunları için hemen çözüm üretebilirim. Ne tür bir sorun yaşıyorsunuz?'
                ],
                'billing_help': [
                    'Faturalama ile ilgili sorularınızı yanıtlayabilirim. Detayları paylaşır mısınız?',
                    'Ödeme ve fatura konularında size yardımcı olabilirim.',
                    'Faturanızla ilgili bir sorun mu var? Hemen çözelim.'
                ]
            },
            'en': {
                'greeting': [
                    'Hello! How can I help you today?',
                    'Welcome to Solutio 360 AI Assistant! I\'m here to help.',
                    'Hi there! I\'m ready to assist with your questions or complaints.'
                ],
                'technical_help': [
                    'I can help with technical issues. Please share the details of your problem.',
                    'You\'re in the right place for technical support. What seems to be the issue?',
                    'I can provide solutions for system problems. What are you experiencing?'
                ],
                'billing_help': [
                    'I can assist with billing questions. Please share the details.',
                    'I\'m here to help with payment and billing matters.',
                    'Is there an issue with your bill? Let\'s resolve it quickly.'
                ]
            }
        };
        
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.createChatUI();
        this.bindEvents();
        this.loadConversationHistory();
        this.isInitialized = true;
        
        // Initialize with greeting
        setTimeout(() => {
            this.addMessage('bot', this.getRandomResponse('greeting'), 'system');
        }, 1000);
        
        console.log('AI Customer Service Chatbot initialized');
    }

    createChatUI() {
        // Create chat container
        this.chatContainer = document.createElement('div');
        this.chatContainer.id = 'ai-chatbot-container';
        this.chatContainer.className = 'ai-chatbot-container hidden';
        this.chatContainer.innerHTML = `
            <div class="ai-chatbot-header">
                <div class="ai-chatbot-title">
                    <div class="ai-chatbot-avatar">🤖</div>
                    <div class="ai-chatbot-info">
                        <h4>Solutio 360 AI Asistan</h4>
                        <span class="ai-chatbot-status online">Çevrimiçi</span>
                    </div>
                </div>
                <button class="ai-chatbot-minimize" title="Küçült">−</button>
            </div>
            <div class="ai-chatbot-messages" id="ai-chatbot-messages">
                <div class="ai-chatbot-typing hidden" id="ai-chatbot-typing">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <span class="typing-text">AI yazıyor...</span>
                </div>
            </div>
            <div class="ai-chatbot-quick-actions">
                <button class="quick-action-btn" data-action="technical">🔧 Teknik Destek</button>
                <button class="quick-action-btn" data-action="billing">💳 Faturalama</button>
                <button class="quick-action-btn" data-action="complaint">📝 Şikayet</button>
            </div>
            <div class="ai-chatbot-input-container">
                <textarea 
                    class="ai-chatbot-input" 
                    id="ai-chatbot-input" 
                    placeholder="Mesajınızı yazın..." 
                    rows="1"></textarea>
                <button class="ai-chatbot-send" id="ai-chatbot-send" title="Gönder">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
            <div class="ai-chatbot-footer">
                <small>🔒 Güvenli ve özel - AI destekli</small>
            </div>
        `;

        // Create toggle button
        this.toggleButton = document.createElement('button');
        this.toggleButton.id = 'ai-chatbot-toggle';
        this.toggleButton.className = 'ai-chatbot-toggle';
        this.toggleButton.innerHTML = `
            <div class="ai-chatbot-toggle-icon">💬</div>
            <div class="ai-chatbot-notification-badge hidden">1</div>
        `;
        this.toggleButton.title = 'AI Müşteri Hizmetleri';

        // Add to DOM
        document.body.appendChild(this.chatContainer);
        document.body.appendChild(this.toggleButton);

        // Get references
        this.messagesContainer = document.getElementById('ai-chatbot-messages');
        this.userInput = document.getElementById('ai-chatbot-input');
        this.sendButton = document.getElementById('ai-chatbot-send');

        // Add CSS
        this.addChatStyles();
    }

    addChatStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .ai-chatbot-container {
                position: fixed;
                bottom: 100px;
                right: 20px;
                width: 380px;
                max-height: 600px;
                background: #ffffff;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                z-index: 10000;
                display: flex;
                flex-direction: column;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                border: 1px solid rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }

            .ai-chatbot-container.hidden {
                transform: translateY(20px) scale(0.95);
                opacity: 0;
                pointer-events: none;
            }

            .ai-chatbot-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-radius: 20px 20px 0 0;
            }

            .ai-chatbot-title {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .ai-chatbot-avatar {
                width: 40px;
                height: 40px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }

            .ai-chatbot-info h4 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }

            .ai-chatbot-status {
                font-size: 12px;
                opacity: 0.9;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .ai-chatbot-status.online::before {
                content: '';
                width: 8px;
                height: 8px;
                background: #4ade80;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }

            .ai-chatbot-minimize {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 5px;
                border-radius: 50%;
                transition: background 0.2s;
            }

            .ai-chatbot-minimize:hover {
                background: rgba(255, 255, 255, 0.1);
            }

            .ai-chatbot-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                max-height: 350px;
                background: #f8fafc;
            }

            .ai-chatbot-message {
                margin-bottom: 16px;
                display: flex;
                gap: 12px;
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .ai-chatbot-message.user {
                flex-direction: row-reverse;
            }

            .ai-chatbot-message-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                flex-shrink: 0;
            }

            .ai-chatbot-message.user .ai-chatbot-message-avatar {
                background: #3b82f6;
                color: white;
            }

            .ai-chatbot-message.bot .ai-chatbot-message-avatar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .ai-chatbot-message-content {
                flex: 1;
                max-width: 70%;
            }

            .ai-chatbot-message-bubble {
                padding: 12px 16px;
                border-radius: 18px;
                position: relative;
                word-wrap: break-word;
                line-height: 1.4;
            }

            .ai-chatbot-message.user .ai-chatbot-message-bubble {
                background: #3b82f6;
                color: white;
                border-bottom-right-radius: 4px;
            }

            .ai-chatbot-message.bot .ai-chatbot-message-bubble {
                background: white;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-bottom-left-radius: 4px;
            }

            .ai-chatbot-message-time {
                font-size: 11px;
                color: #9ca3af;
                margin-top: 4px;
                text-align: center;
            }

            .ai-chatbot-message.user .ai-chatbot-message-time {
                text-align: right;
            }

            .ai-chatbot-message.bot .ai-chatbot-message-time {
                text-align: left;
            }

            .ai-chatbot-typing {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 16px;
                background: white;
                border-radius: 18px;
                border: 1px solid #e5e7eb;
                margin-bottom: 16px;
                animation: slideIn 0.3s ease-out;
            }

            .typing-indicator {
                display: flex;
                gap: 4px;
            }

            .typing-indicator span {
                width: 6px;
                height: 6px;
                background: #9ca3af;
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }

            .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
            .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

            @keyframes typing {
                0%, 80%, 100% { 
                    transform: scale(0.8);
                    opacity: 0.5;
                }
                40% { 
                    transform: scale(1);
                    opacity: 1;
                }
            }

            .typing-text {
                font-size: 12px;
                color: #6b7280;
            }

            .ai-chatbot-quick-actions {
                padding: 16px 20px;
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                background: white;
                border-top: 1px solid #e5e7eb;
            }

            .quick-action-btn {
                padding: 8px 12px;
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 20px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                color: #4b5563;
            }

            .quick-action-btn:hover {
                background: #e5e7eb;
                transform: translateY(-1px);
            }

            .ai-chatbot-input-container {
                padding: 20px;
                background: white;
                display: flex;
                gap: 12px;
                align-items: flex-end;
                border-top: 1px solid #e5e7eb;
            }

            .ai-chatbot-input {
                flex: 1;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 12px 16px;
                resize: none;
                font-family: inherit;
                font-size: 14px;
                line-height: 1.4;
                transition: border-color 0.2s;
                max-height: 100px;
                outline: none;
            }

            .ai-chatbot-input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .ai-chatbot-send {
                width: 44px;
                height: 44px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 12px;
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                flex-shrink: 0;
            }

            .ai-chatbot-send:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .ai-chatbot-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }

            .ai-chatbot-footer {
                padding: 12px 20px;
                background: #f9fafb;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                border-radius: 0 0 20px 20px;
            }

            .ai-chatbot-footer small {
                color: #6b7280;
                font-size: 11px;
            }

            .ai-chatbot-toggle {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 50%;
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
                z-index: 9999;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
            }

            .ai-chatbot-toggle:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
            }

            .ai-chatbot-notification-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                width: 20px;
                height: 20px;
                background: #ef4444;
                color: white;
                border-radius: 50%;
                font-size: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: bounce 1s infinite;
            }

            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-3px); }
                60% { transform: translateY(-2px); }
            }

            .hidden {
                display: none !important;
            }

            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .ai-chatbot-container {
                    width: calc(100vw - 40px);
                    right: 20px;
                    left: 20px;
                    bottom: 90px;
                    max-height: 70vh;
                }

                .ai-chatbot-messages {
                    max-height: calc(50vh - 100px);
                }
            }

            /* Accessibility improvements */
            .ai-chatbot-container:focus-within {
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15), 0 0 0 2px #667eea;
            }

            .ai-chatbot-input:focus,
            .ai-chatbot-send:focus,
            .quick-action-btn:focus {
                outline: 2px solid #667eea;
                outline-offset: 2px;
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // Toggle chat
        this.toggleButton.addEventListener('click', () => {
            this.toggleChat();
        });

        // Minimize chat
        this.chatContainer.querySelector('.ai-chatbot-minimize').addEventListener('click', () => {
            this.toggleChat();
        });

        // Send message
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Input events
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = Math.min(this.userInput.scrollHeight, 100) + 'px';
        });

        // Quick actions
        this.chatContainer.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }

    toggleChat() {
        const isHidden = this.chatContainer.classList.contains('hidden');
        
        if (isHidden) {
            this.chatContainer.classList.remove('hidden');
            this.userInput.focus();
            this.hideNotificationBadge();
        } else {
            this.chatContainer.classList.add('hidden');
        }
    }

    showNotificationBadge(count = 1) {
        const badge = this.toggleButton.querySelector('.ai-chatbot-notification-badge');
        badge.textContent = count;
        badge.classList.remove('hidden');
    }

    hideNotificationBadge() {
        const badge = this.toggleButton.querySelector('.ai-chatbot-notification-badge');
        badge.classList.add('hidden');
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isTyping) return;

        // Add user message
        this.addMessage('user', message);
        this.userInput.value = '';
        this.userInput.style.height = 'auto';

        // Show typing indicator
        this.showTyping();

        try {
            // Process message with AI
            const response = await this.processWithAI(message);
            
            // Hide typing and show response
            this.hideTyping();
            this.addMessage('bot', response.message || response.auto_response, 'ai');

            // Update conversation history
            this.conversationHistory.push({
                user: message,
                bot: response.message || response.auto_response,
                timestamp: new Date().toISOString(),
                analysis: response.analysis
            });

            this.saveConversationHistory();

        } catch (error) {
            console.error('AI processing error:', error);
            this.hideTyping();
            this.addMessage('bot', 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin veya müsteri hizmetlerimizle iletişime geçin.', 'error');
        }
    }

    async processWithAI(message) {
        // Check for simple patterns first
        const simpleResponse = this.getSimpleResponse(message);
        if (simpleResponse) {
            return { message: simpleResponse };
        }

        // Process with backend AI
        const formData = new FormData();
        formData.append('complaint_text', message);

        const response = await fetch(this.apiEndpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    getSimpleResponse(message) {
        const lowerMessage = message.toLowerCase();
        
        // Greeting patterns
        if (lowerMessage.match(/^(merhaba|selam|hello|hi|hey)\b/)) {
            return this.getRandomResponse('greeting');
        }

        // Technical help patterns
        if (lowerMessage.includes('teknik') || lowerMessage.includes('technical') || 
            lowerMessage.includes('sistem') || lowerMessage.includes('hata')) {
            return this.getRandomResponse('technical_help');
        }

        // Billing help patterns
        if (lowerMessage.includes('fatura') || lowerMessage.includes('ödeme') || 
            lowerMessage.includes('billing') || lowerMessage.includes('payment')) {
            return this.getRandomResponse('billing_help');
        }

        return null;
    }

    getRandomResponse(type) {
        const language = this.detectLanguage();
        const responses = this.quickResponses[language] && this.quickResponses[language][type];
        
        if (responses && responses.length > 0) {
            return responses[Math.floor(Math.random() * responses.length)];
        }
        
        return 'Size nasıl yardımcı olabilirim?';
    }

    detectLanguage() {
        // Simple language detection - could be enhanced
        return 'tr'; // Default to Turkish
    }

    handleQuickAction(action) {
        const messages = {
            'technical': 'Teknik bir sorun yaşıyorum, yardım edebilir misiniz?',
            'billing': 'Faturalama konusunda bir sorum var.',
            'complaint': 'Bir şikayetim var ve çözüm istiyorum.'
        };

        if (messages[action]) {
            this.userInput.value = messages[action];
            this.sendMessage();
        }
    }

    showTyping() {
        this.isTyping = true;
        const typingElement = document.getElementById('ai-chatbot-typing');
        typingElement.classList.remove('hidden');
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        const typingElement = document.getElementById('ai-chatbot-typing');
        typingElement.classList.add('hidden');
    }

    addMessage(sender, content, type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-chatbot-message ${sender}`;
        
        const avatar = sender === 'user' ? '👤' : '🤖';
        const time = new Date().toLocaleTimeString('tr-TR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageDiv.innerHTML = `
            <div class="ai-chatbot-message-avatar">${avatar}</div>
            <div class="ai-chatbot-message-content">
                <div class="ai-chatbot-message-bubble">${content}</div>
                <div class="ai-chatbot-message-time">${time}</div>
            </div>
        `;

        // Insert before typing indicator
        const typingElement = document.getElementById('ai-chatbot-typing');
        this.messagesContainer.insertBefore(messageDiv, typingElement);
        
        this.scrollToBottom();

        // Show notification if chat is closed
        if (sender === 'bot' && this.chatContainer.classList.contains('hidden')) {
            this.showNotificationBadge();
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        
        for (let cookie of cookies) {
            const [cookieName, cookieValue] = cookie.trim().split('=');
            if (cookieName === name) {
                return decodeURIComponent(cookieValue);
            }
        }
        
        // Fallback: get from meta tag
        const metaTag = document.querySelector('meta[name=csrf-token]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    saveConversationHistory() {
        try {
            localStorage.setItem('ai_chatbot_history', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.warn('Could not save conversation history:', error);
        }
    }

    loadConversationHistory() {
        try {
            const history = localStorage.getItem('ai_chatbot_history');
            if (history) {
                this.conversationHistory = JSON.parse(history);
                
                // Load last few messages
                const recentMessages = this.conversationHistory.slice(-5);
                recentMessages.forEach(msg => {
                    this.addMessage('user', msg.user);
                    this.addMessage('bot', msg.bot, 'ai');
                });
            }
        } catch (error) {
            console.warn('Could not load conversation history:', error);
        }
    }

    // Public API methods
    open() {
        this.chatContainer.classList.remove('hidden');
        this.userInput.focus();
        this.hideNotificationBadge();
    }

    close() {
        this.chatContainer.classList.add('hidden');
    }

    sendPredefinedMessage(message) {
        this.userInput.value = message;
        this.sendMessage();
    }

    clearHistory() {
        this.conversationHistory = [];
        this.messagesContainer.innerHTML = `
            <div class="ai-chatbot-typing hidden" id="ai-chatbot-typing">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="typing-text">AI yazıyor...</span>
            </div>
        `;
        this.saveConversationHistory();
        
        // Add greeting message
        setTimeout(() => {
            this.addMessage('bot', this.getRandomResponse('greeting'), 'system');
        }, 500);
    }
}

// Global instance
let aiChatbot = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    aiChatbot = new AICustomerServiceChatbot({
        apiEndpoint: '/analytics/api/process-complaint-ai/',
        autoResponseEndpoint: '/analytics/api/auto-response/',
        sentimentEndpoint: '/analytics/api/sentiment-analysis/'
    });
    
    // Global access
    window.aiChatbot = aiChatbot;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AICustomerServiceChatbot;
} 