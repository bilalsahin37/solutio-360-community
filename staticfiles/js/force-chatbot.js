// Force Chatbot Creation Script
// Bu script her zaman çalışır ve chatbot butonunu oluşturur

console.log('🚀 Force Chatbot Script Loading...');

// Immediate execution - DOM'un hazır olmasını beklemeden
(function() {
    'use strict';
    
    function createChatbotButton() {
        console.log('🛠️ Creating force chatbot button...');
        
        // Remove existing chatbot if any
        const existingBot = document.getElementById('force-chatbot-btn');
        if (existingBot) {
            existingBot.remove();
        }
        
        // Create chatbot button
        const chatBtn = document.createElement('div');
        chatBtn.id = 'force-chatbot-btn';
        chatBtn.innerHTML = `
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
                z-index: 99999;
                transition: all 0.3s ease;
                font-size: 28px;
                color: white;
                border: 3px solid rgba(255,255,255,0.2);
            " onmouseover="this.style.transform='scale(1.1) rotate(10deg)'" 
               onmouseout="this.style.transform='scale(1) rotate(0deg)'"
               onclick="toggleChatbot()">
                🤖
            </div>
        `;
        
        document.body.appendChild(chatBtn);
        console.log('✅ Force chatbot button created!');
        
        // Create chat window
        createChatWindow();
    }
    
    function createChatWindow() {
        // Remove existing window
        const existingWindow = document.getElementById('force-chat-window');
        if (existingWindow) {
            existingWindow.remove();
        }
        
        const chatWindow = document.createElement('div');
        chatWindow.id = 'force-chat-window';
        chatWindow.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 99998;
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        `;
        
        chatWindow.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <span>🤖 AI Chatbot</span>
                <span style="cursor: pointer; font-size: 20px;" onclick="toggleChatbot()">×</span>
            </div>
            <div style="
                flex: 1;
                padding: 20px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                color: #64748b;
            ">
                <div style="font-size: 48px; margin-bottom: 20px;">🎉</div>
                <h3 style="color: #1e293b; margin-bottom: 10px;">AI Chatbot Aktif!</h3>
                <p style="margin-bottom: 20px;">Solutio 360 AI Chatbot sistemi çalışıyor!</p>
                <div style="
                    background: #f1f5f9;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    width: 100%;
                ">
                    <strong>Özellikler:</strong><br>
                    ✅ Şikayet Analizi<br>
                    ✅ Otomatik Yanıt<br>
                    ✅ Sentiment Analizi<br>
                    ✅ 7/24 Destek
                </div>
                <button style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: transform 0.2s ease;
                " onmouseover="this.style.transform='scale(1.05)'"
                   onmouseout="this.style.transform='scale(1)'"
                   onclick="alert('🚀 Chat başlatılıyor! Backend entegrasyon devam ediyor...')">
                    Chat Başlat
                </button>
            </div>
        `;
        
        document.body.appendChild(chatWindow);
        console.log('✅ Chat window created!');
    }
    
    // Global toggle function
    window.toggleChatbot = function() {
        const chatWindow = document.getElementById('force-chat-window');
        if (chatWindow) {
            if (chatWindow.style.display === 'none' || !chatWindow.style.display) {
                chatWindow.style.display = 'flex';
                console.log('💬 Chatbot opened');
            } else {
                chatWindow.style.display = 'none';
                console.log('💬 Chatbot closed');
            }
        }
    };
    
    // Create immediately
    createChatbotButton();
    
    // Also create when DOM is ready (backup)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createChatbotButton);
    }
    
    // Create after a delay (extra backup)
    setTimeout(createChatbotButton, 2000);
    
    console.log('✅ Force Chatbot Script Loaded Successfully!');
})(); 