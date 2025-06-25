// Chat Z-Index Fix - CDN Free Solution
console.log('🔧 Chat Z-Index Fix Loading...');

document.addEventListener('DOMContentLoaded', function() {
    // Remove duplicate chat widgets
    const existingChats = document.querySelectorAll('[id*="clean-chat"], [id*="chat-window"], [id*="chat-btn"]');
    console.log('🗑️ Removing', existingChats.length, 'existing chat elements');
    existingChats.forEach(el => el.remove());
    
    // Create fixed chat widget
    const chatHTML = `
        <div id="fixed-chat-container" style="
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 999999 !important;
            font-family: Arial, sans-serif;
        ">
            <button id="fixed-chat-btn" style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                border: none;
                background: #007bff;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 6px 20px rgba(0,123,255,0.4);
                transition: transform 0.3s;
                z-index: 999998 !important;
                position: relative;
            ">💬</button>
            
            <div id="fixed-chat-window" style="
                position: fixed !important;
                bottom: 90px !important;
                right: 20px !important;
                width: 350px !important;
                height: 500px !important;
                background: white !important;
                border: 2px solid #007bff !important;
                border-radius: 15px !important;
                box-shadow: 0 15px 35px rgba(0,0,0,0.3) !important;
                display: none;
                flex-direction: column;
                z-index: 999999 !important;
                overflow: hidden;
            ">
                <div style="
                    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                    color: white;
                    padding: 18px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-radius: 13px 13px 0 0;
                ">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 10px; height: 10px; background: #28a745; border-radius: 50%; animation: pulse 2s infinite;"></div>
                        <strong>AI Asistan</strong>
                    </div>
                    <button id="fixed-close-chat" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 22px;
                        cursor: pointer;
                        padding: 5px;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">&times;</button>
                </div>
                
                <div id="fixed-messages" style="
                    flex: 1;
                    padding: 20px;
                    overflow-y: auto;
                    background: #f8f9fa;
                    max-height: 350px;
                ">
                    <div style="
                        background: #e9ecef;
                        color: #333;
                        padding: 12px 16px;
                        border-radius: 18px;
                        margin-bottom: 12px;
                        max-width: 85%;
                        animation: slideIn 0.3s ease;
                    ">
                        Merhaba! Ben AI asistanınızım. Size nasıl yardımcı olabilirim? 🤖
                    </div>
                </div>
                
                <div style="
                    padding: 20px;
                    display: flex;
                    gap: 12px;
                    border-top: 1px solid #eee;
                    background: white;
                    border-radius: 0 0 13px 13px;
                ">
                    <input type="text" id="fixed-msg-input" placeholder="Mesajınızı yazın..." style="
                        flex: 1;
                        padding: 14px 18px;
                        border: 2px solid #ddd;
                        border-radius: 25px;
                        outline: none;
                        font-size: 14px;
                        transition: border-color 0.3s;
                    ">
                    <button id="fixed-send-btn" style="
                        padding: 14px 20px;
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 25px;
                        cursor: pointer;
                        font-weight: 600;
                        transition: all 0.3s;
                    ">Gönder</button>
                </div>
            </div>
        </div>
    `;
    
    // Add to body
    document.body.insertAdjacentHTML('beforeend', chatHTML);
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        #fixed-msg-input:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.1) !important;
        }
        #fixed-send-btn:hover {
            background: #0056b3 !important;
            transform: translateY(-1px);
        }
        #fixed-chat-btn:hover {
            transform: scale(1.1) !important;
        }
    `;
    document.head.appendChild(style);
    
    // Variables
    let chatOpen = false;
    
    // Functions
    function toggleFixedChat() {
        console.log('🔄 Fixed chat toggle clicked');
        const chatWindow = document.getElementById('fixed-chat-window');
        const chatContainer = document.getElementById('fixed-chat-container');
        const chatBtn = document.getElementById('fixed-chat-btn');
        
        chatOpen = !chatOpen;
        
        if (chatOpen) {
            // Force z-index to highest values
            chatContainer.style.zIndex = '999999';
            chatWindow.style.position = 'fixed';
            chatWindow.style.bottom = '90px';
            chatWindow.style.right = '20px';
            chatWindow.style.zIndex = '999999';
            chatWindow.style.display = 'flex';
            chatBtn.style.zIndex = '999998';
            
            console.log('✅ Fixed chat açıldı - Z-index:', chatWindow.style.zIndex);
            
            setTimeout(() => {
                const input = document.getElementById('fixed-msg-input');
                if (input) {
                    input.focus();
                    console.log('📝 Input focused');
                }
            }, 100);
        } else {
            chatWindow.style.display = 'none';
            console.log('❌ Fixed chat kapatıldı');
        }
    }
    
    function closeFixedChat() {
        console.log('🔄 Close fixed chat clicked');
        chatOpen = false;
        const chatWindow = document.getElementById('fixed-chat-window');
        if (chatWindow) {
            chatWindow.style.display = 'none';
        }
    }
    
    function addFixedMessage(text, isUser = false) {
        const messages = document.getElementById('fixed-messages');
        if (!messages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            background: ${isUser ? '#007bff' : '#e9ecef'};
            color: ${isUser ? 'white' : '#333'};
            padding: 12px 16px;
            border-radius: 18px;
            margin-bottom: 12px;
            max-width: 85%;
            word-wrap: break-word;
            animation: slideIn 0.3s ease;
            ${isUser ? 'margin-left: auto; text-align: right;' : ''}
        `;
        messageDiv.textContent = text;
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
        
        console.log(`💬 Fixed message added: ${text.substring(0, 30)}...`);
    }
    
    function showFixedTyping() {
        const messages = document.getElementById('fixed-messages');
        if (!messages) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.id = 'fixed-typing-indicator';
        typingDiv.style.cssText = `
            background: #e9ecef;
            color: #666;
            padding: 12px 16px;
            border-radius: 18px;
            margin-bottom: 12px;
            font-style: italic;
            max-width: 85%;
            animation: pulse 1.5s infinite;
        `;
        typingDiv.innerHTML = '💭 AI yazıyor...';
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;
    }
    
    function hideFixedTyping() {
        const typing = document.getElementById('fixed-typing-indicator');
        if (typing) typing.remove();
    }
    
    async function sendFixedMessage() {
        const input = document.getElementById('fixed-msg-input');
        if (!input) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        console.log('📤 Fixed message sending:', message);
        
        addFixedMessage(message, true);
        input.value = '';
        showFixedTyping();
        
        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            hideFixedTyping();
            
            console.log('📥 Fixed API response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('📥 Fixed API response data:', data);
                addFixedMessage(data.response || data.message || 'Yanıt alınamadı.');
            } else {
                const errorText = await response.text();
                console.error('❌ Fixed API Error:', response.status, errorText);
                addFixedMessage(`Bağlantı hatası (${response.status}). Tekrar deneyin.`);
            }
        } catch (error) {
            hideFixedTyping();
            console.error('❌ Fixed Network Error:', error);
            addFixedMessage('Ağ hatası. İnternet bağlantınızı kontrol edin.');
        }
    }
    
    // Event Listeners
    const chatBtn = document.getElementById('fixed-chat-btn');
    const closeBtn = document.getElementById('fixed-close-chat');
    const sendBtn = document.getElementById('fixed-send-btn');
    const msgInput = document.getElementById('fixed-msg-input');
    
    if (chatBtn) chatBtn.onclick = toggleFixedChat;
    if (closeBtn) closeBtn.onclick = closeFixedChat;
    if (sendBtn) sendBtn.onclick = sendFixedMessage;
    if (msgInput) {
        msgInput.onkeypress = function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendFixedMessage();
            }
        };
    }
    
    // Test z-index values
    console.log('🎯 Fixed chat container z-index:', document.getElementById('fixed-chat-container')?.style.zIndex || 'default');
    
    // API connection test
    fetch('/api/chat/', { method: 'OPTIONS' })
        .then(response => {
            if (response.ok || response.status === 405) {
                console.log('✅ Fixed API endpoint accessible');
            } else {
                console.warn('⚠️ Fixed API endpoint issue:', response.status);
            }
        })
        .catch(error => {
            console.error('❌ Fixed API test error:', error);
        });
    
    console.log('✅ Fixed Chat Widget completely ready!');
});

// Export for global access
window.toggleFixedChat = function() {
    const btn = document.getElementById('fixed-chat-btn');
    if (btn) btn.click();
}; 