// Simple Chat Widget - Clean Implementation
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat.js loaded');
    
    // Remove any existing chat elements first
    document.querySelectorAll('[id*="chat"], [class*="chat"]').forEach(el => {
        if (el.id !== 'chat-btn' && el.id !== 'chat-window') {
            el.remove();
        }
    });
    
    // Check if elements already exist
    if (!document.getElementById('chat-btn')) {
        createChatWidget();
    }
});

function createChatWidget() {
    const chatHTML = `
        <div id="chat-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 10000; font-family: Arial, sans-serif;">
            <button id="chat-btn" style="
                width: 60px; height: 60px; border-radius: 50%; border: none;
                background: #007bff; color: white; font-size: 24px; cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.2s;
            ">💬</button>
            
            <div id="chat-window" style="
                position: absolute; bottom: 70px; right: 0; width: 320px; height: 400px;
                background: white; border: 1px solid #ddd; border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15); display: none; flex-direction: column;
            ">
                <div style="background: #007bff; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-radius: 12px 12px 0 0;">
                    <span><strong>AI Asistan</strong></span>
                    <button id="close-chat" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer;">&times;</button>
                </div>
                
                <div id="messages" style="flex: 1; padding: 15px; overflow-y: auto; background: #f8f9fa;">
                    <div style="background: #e9ecef; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; max-width: 85%;">
                        Merhaba! Size nasıl yardımcı olabilirim?
                    </div>
                </div>
                
                <div style="padding: 15px; display: flex; gap: 10px; border-top: 1px solid #eee;">
                    <input type="text" id="message-input" placeholder="Mesajınızı yazın..." style="
                        flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none;
                    ">
                    <button id="send-btn" style="
                        padding: 12px 18px; background: #007bff; color: white; border: none; border-radius: 25px; cursor: pointer;
                    ">Gönder</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', chatHTML);
    
    // Bind events
    document.getElementById('chat-btn').onclick = toggleChat;
    document.getElementById('close-chat').onclick = closeChat;
    document.getElementById('send-btn').onclick = sendMessage;
    document.getElementById('message-input').onkeypress = function(e) {
        if (e.key === 'Enter') sendMessage();
    };
    
    // Hover effects
    const chatBtn = document.getElementById('chat-btn');
    chatBtn.onmouseenter = () => chatBtn.style.transform = 'scale(1.1)';
    chatBtn.onmouseleave = () => chatBtn.style.transform = 'scale(1)';
    
    console.log('✅ Chat widget created successfully');
}

let chatOpen = false;

function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    chatOpen = !chatOpen;
    chatWindow.style.display = chatOpen ? 'flex' : 'none';
    
    if (chatOpen) {
        setTimeout(() => {
            const input = document.getElementById('message-input');
            if (input) input.focus();
        }, 100);
    }
}

function closeChat() {
    chatOpen = false;
    const chatWindow = document.getElementById('chat-window');
    if (chatWindow) {
        chatWindow.style.display = 'none';
    }
}

function addMessage(text, isUser = false) {
    const messages = document.getElementById('messages');
    if (!messages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
        background: ${isUser ? '#007bff' : '#e9ecef'};
        color: ${isUser ? 'white' : '#333'};
        padding: 10px 15px; border-radius: 18px; margin-bottom: 10px;
        max-width: 85%; word-wrap: break-word;
        ${isUser ? 'margin-left: auto; text-align: right;' : ''}
    `;
    messageDiv.textContent = text;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

function showTyping() {
    const messages = document.getElementById('messages');
    if (!messages) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing';
    typingDiv.style.cssText = 'background: #e9ecef; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; font-style: italic; max-width: 85%;';
    typingDiv.textContent = 'AI yazıyor...';
    messages.appendChild(typingDiv);
    messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typing');
    if (typing) typing.remove();
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(message, true);
    input.value = '';
    
    // Show typing indicator
    showTyping();
    
    try {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ message: message })
        });
        
        hideTyping();
        
        if (response.ok) {
            const data = await response.json();
            addMessage(data.response || data.message || 'Yanıt alınamadı.');
        } else {
            addMessage('Bağlantı hatası. Lütfen tekrar deneyin.');
        }
    } catch (error) {
        hideTyping();
        addMessage('Ağ hatası. Lütfen tekrar deneyin.');
        console.error('Chat error:', error);
    }
}

function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
} 