/**
 * Solutio 360 - Şikayet Yönetimi JavaScript Modülü
 * ===============================================
 * 
 * Bu modül şikayet sistemi için frontend işlevselliği sağlar:
 * - Şikayet geri çekme işlemleri
 * - Şikayet iptal etme işlemleri
 * - Şikayet silme işlemleri
 * - AJAX tabanlı durum güncellemeleri
 * - Modal dialog yönetimi
 * - Bildirim sistemi
 * - Otomatik kaydetme özelliği
 * - Form validasyonu
 * 
 * Sınıf Yapısı:
 * - ComplaintManager: Ana şikayet yönetim sınıfı
 * 
 * Kullanım:
 * const complaintManager = new ComplaintManager();
 * 
 * @author Solutio 360 Development Team
 * @version 1.0.0
 */

class ComplaintManager {
    /**
     * ComplaintManager sınıf yapıcısı.
     * 
     * Şikayet yönetimi için gerekli temel ayarları yapar ve
     * event listener'ları başlatır.
     */
    constructor() {
        // API base URL'i - tüm şikayet işlemleri için
        this.baseUrl = '/complaints/';
        
        // Otomatik kaydetme interval ID'si
        this.autoSaveInterval = null;
        
        // Modal açık durumu kontrolü
        this.isModalOpen = false;
        
        // Sınıfı başlat
        this.init();
    }

    /**
     * Sınıf başlatma metodu.
     * 
     * Tüm event listener'ları ve temel ayarları yapar.
     */
    init() {
        this.bindEvents();        // Event listener'ları bağla
        this.initModals();        // Modal ayarlarını yap
        this.initConfirmations(); // Onay dialog'larını ayarla
        this.initTooltips();      // Tooltip'leri başlat
        this.initAutoComplete();  // Otomatik tamamlama
    }

    /**
     * Event listener'ları DOM elementlerine bağlar.
     * 
     * Şikayet işlemleri için gerekli buton ve form event'lerini
     * ilgili metodlara yönlendirir.
     */
    bindEvents() {
        // Şikayet geri çekme butonları
        document.querySelectorAll('.withdraw-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault(); // Varsayılan link davranışını engelle
                
                // Buton üzerindeki data attribute'lardan bilgileri al
                const complaintId = btn.dataset.complaintId;
                const complaintTitle = btn.dataset.complaintTitle;
                
                // Geri çekme modal'ını göster
                this.showWithdrawModal(complaintId, complaintTitle);
            });
        });

        // Şikayet iptal etme butonları
        document.querySelectorAll('.cancel-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault(); // Varsayılan link davranışını engelle
                
                // Buton verilerini al
                const complaintId = btn.dataset.complaintId;
                const complaintTitle = btn.dataset.complaintTitle;
                
                // İptal modal'ını göster
                this.showCancelModal(complaintId, complaintTitle);
            });
        });

        // Şikayet silme butonları
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault(); // Varsayılan link davranışını engelle
                
                // Buton verilerini al
                const complaintId = btn.dataset.complaintId;
                const complaintTitle = btn.dataset.complaintTitle;
                
                // Silme onayı göster
                this.showDeleteConfirmation(complaintId, complaintTitle);
            });
        });

        // Durum güncelleme butonları
        document.querySelectorAll('.status-update-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                const complaintId = btn.dataset.complaintId;
                const newStatus = btn.dataset.newStatus;
                
                // Durum güncelleme modal'ını göster
                this.showStatusUpdateModal(complaintId, newStatus);
            });
        });
    }

    /**
     * Modal dialog ayarlarını yapar.
     * 
     * Modal kapatma event'lerini ve keyboard shortcut'larını ayarlar.
     */
    initModals() {
        // Modal backdrop'a tıklayınca kapatma
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.closeAllModals();
            }
        });

        // ESC tuşu ile modal kapatma
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen) {
                this.closeAllModals();
            }
        });

        // Modal içindeki kapatma butonları
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close')) {
                this.closeAllModals();
            }
        });
    }

    /**
     * Form onay dialog'larını başlatır.
     * 
     * Kritik işlemler için kullanıcı onayı alır.
     */
    initConfirmations() {
        // Onay gerektiren formlar
        document.querySelectorAll('.confirm-form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const confirmMessage = form.dataset.confirmMessage || 
                    'Bu işlemi gerçekleştirmek istediğinizden emin misiniz?';
                
                if (!this.confirmAction(confirmMessage)) {
                    e.preventDefault(); // Form gönderimini engelle
                }
            });
        });
    }

    /**
     * Tooltip'leri başlatır.
     * 
     * Kullanıcı arayüzündeki yardım ipuçlarını aktif eder.
     */
    initTooltips() {
        // Tooltip gerektiren elementler
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    /**
     * Otomatik tamamlama özelliğini başlatır.
     * 
     * Form alanlarında otomatik tamamlama sağlar.
     */
    initAutoComplete() {
        // Otomatik tamamlama alanları
        document.querySelectorAll('.autocomplete').forEach(input => {
            input.addEventListener('input', (e) => {
                this.handleAutoComplete(e.target);
            });
        });
    }

    /**
     * Şikayet geri çekme modal'ını gösterir.
     * 
     * @param {string} complaintId - Şikayet UUID'si
     * @param {string} complaintTitle - Şikayet başlığı
     */
    showWithdrawModal(complaintId, complaintTitle) {
        const modal = this.createModal('withdraw', {
            title: 'Şikayeti Geri Çek',
            complaintId: complaintId,
            complaintTitle: complaintTitle,
            actionUrl: `${this.baseUrl}${complaintId}/withdraw/`,
            submitText: 'Geri Çek',
            submitClass: 'bg-orange-500 hover:bg-orange-600',
            reasonRequired: false, // Geri çekme sebebi isteğe bağlı
            iconClass: 'text-orange-500'
        });
        
        // Modal'ı DOM'a ekle ve göster
        document.body.appendChild(modal);
        this.isModalOpen = true;
        
        // Modal animasyonu için kısa gecikme
        setTimeout(() => {
            modal.classList.add('modal-show');
        }, 10);
    }

    /**
     * Şikayet iptal etme modal'ını gösterir.
     * 
     * @param {string} complaintId - Şikayet UUID'si
     * @param {string} complaintTitle - Şikayet başlığı
     */
    showCancelModal(complaintId, complaintTitle) {
        const modal = this.createModal('cancel', {
            title: 'Şikayeti İptal Et',
            complaintId: complaintId,
            complaintTitle: complaintTitle,
            actionUrl: `${this.baseUrl}${complaintId}/cancel/`,
            submitText: 'İptal Et',
            submitClass: 'bg-red-500 hover:bg-red-600',
            reasonRequired: true, // İptal sebebi zorunlu
            iconClass: 'text-red-500'
        });
        
        // Modal'ı DOM'a ekle ve göster
        document.body.appendChild(modal);
        this.isModalOpen = true;
        
        // Modal animasyonu
        setTimeout(() => {
            modal.classList.add('modal-show');
        }, 10);
    }

    /**
     * Şikayet silme onayı gösterir.
     * 
     * @param {string} complaintId - Şikayet UUID'si
     * @param {string} complaintTitle - Şikayet başlığı
     */
    showDeleteConfirmation(complaintId, complaintTitle) {
        const message = `"${complaintTitle}" başlıklı şikayeti kalıcı olarak silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!`;
        
        // Kullanıcı onayı al
        if (this.confirmAction(message)) {
            // Silme işlemini gerçekleştir
            window.location.href = `${this.baseUrl}${complaintId}/delete-draft/`;
        }
    }

    /**
     * Durum güncelleme modal'ını gösterir.
     * 
     * @param {string} complaintId - Şikayet UUID'si
     * @param {string} newStatus - Yeni durum
     */
    showStatusUpdateModal(complaintId, newStatus) {
        const statusTexts = {
            'IN_REVIEW': 'İncelemeye Al',
            'IN_PROGRESS': 'İşleme Al',
            'RESOLVED': 'Çözüldü Olarak İşaretle',
            'CLOSED': 'Kapat',
            'REOPENED': 'Yeniden Aç'
        };
        
        const modal = this.createModal('status', {
            title: `Şikayet Durumu: ${statusTexts[newStatus] || newStatus}`,
            complaintId: complaintId,
            actionUrl: `${this.baseUrl}${complaintId}/update_status/`,
            submitText: 'Durumu Güncelle',
            submitClass: 'bg-blue-500 hover:bg-blue-600',
            reasonRequired: false,
            statusField: newStatus,
            iconClass: 'text-blue-500'
        });
        
        document.body.appendChild(modal);
        this.isModalOpen = true;
        
        setTimeout(() => {
            modal.classList.add('modal-show');
        }, 10);
    }

    /**
     * Modal dialog oluşturur.
     * 
     * @param {string} type - Modal türü (withdraw, cancel, status)
     * @param {Object} options - Modal seçenekleri
     * @returns {HTMLElement} Modal element
     */
    createModal(type, options) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 z-50 modal-backdrop transition-opacity duration-300';
        modal.id = `${type}Modal`;

        // Modal türüne göre etiket ve placeholder metinleri
        const reasonLabel = this.getReasonLabel(type);
        const reasonPlaceholder = this.getReasonPlaceholder(type);
        const iconSvg = this.getModalIcon(type);

        modal.innerHTML = `
            <div class="flex justify-center items-center h-full p-4">
                <div class="bg-white rounded-lg shadow-xl max-w-md w-full transform transition-all duration-300 scale-95 modal-content">
                    <!-- Modal Header -->
                    <div class="flex items-center justify-between p-6 border-b border-gray-200">
                        <div class="flex items-center space-x-3">
                            <div class="${options.iconClass}">
                                ${iconSvg}
                            </div>
                            <h3 class="text-lg font-semibold text-gray-900">${options.title}</h3>
                        </div>
                        <button type="button" class="modal-close text-gray-400 hover:text-gray-600 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    
                    <!-- Modal Body -->
                    <div class="p-6">
                    <p class="text-gray-600 mb-4">
                            ${this.getModalMessage(type, options.complaintTitle)}
                    </p>
                    
                    <form method="post" action="${options.actionUrl}" class="space-y-4">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${this.getCsrfToken()}">
                            ${options.statusField ? `<input type="hidden" name="status" value="${options.statusField}">` : ''}
                        
                        <div>
                            <label for="${type}_reason" class="block text-sm font-medium text-gray-700 mb-2">
                                ${reasonLabel}${options.reasonRequired ? ' <span class="text-red-500">*</span>' : ' (isteğe bağlı):'}
                            </label>
                                <textarea id="${type}_reason" name="${this.getReasonFieldName(type)}" 
                                      rows="3" ${options.reasonRequired ? 'required' : ''}
                                          class="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                      placeholder="${reasonPlaceholder}"></textarea>
                        </div>
                        
                            <!-- Modal Footer -->
                            <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                                <button type="button" class="modal-close px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500">
                                Vazgeç
                            </button>
                            <button type="submit" 
                                        class="px-4 py-2 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${options.submitClass}">
                                ${options.submitText}
                            </button>
                        </div>
                    </form>
                    </div>
                </div>
            </div>
        `;

        return modal;
    }

    /**
     * Modal türüne göre sebep etiketini döndürür.
     * 
     * @param {string} type - Modal türü
     * @returns {string} Sebep etiketi
     */
    getReasonLabel(type) {
        const labels = {
            'withdraw': 'Geri Çekme Sebebi',
            'cancel': 'İptal Sebebi',
            'status': 'Durum Değişikliği Notu'
        };
        return labels[type] || 'Sebep';
    }

    /**
     * Modal türüne göre placeholder metnini döndürür.
     * 
     * @param {string} type - Modal türü
     * @returns {string} Placeholder metni
     */
    getReasonPlaceholder(type) {
        const placeholders = {
            'withdraw': 'Neden bu şikayeti geri çekiyorsunuz?',
            'cancel': 'Bu şikayeti neden iptal ediyorsunuz?',
            'status': 'Durum değişikliği ile ilgili notunuz...'
        };
        return placeholders[type] || 'Açıklama yazınız...';
    }

    /**
     * Modal türüne göre form field adını döndürür.
     * 
     * @param {string} type - Modal türü
     * @returns {string} Form field adı
     */
    getReasonFieldName(type) {
        const fieldNames = {
            'withdraw': 'withdrawal_reason',
            'cancel': 'cancellation_reason',
            'status': 'status_note'
        };
        return fieldNames[type] || 'reason';
    }

    /**
     * Modal türüne göre mesaj metnini döndürür.
     * 
     * @param {string} type - Modal türü
     * @param {string} complaintTitle - Şikayet başlığı
     * @returns {string} Modal mesajı
     */
    getModalMessage(type, complaintTitle) {
        const messages = {
            'withdraw': `"<strong>${complaintTitle}</strong>" başlıklı şikayeti geri çekmek istediğinizden emin misiniz?`,
            'cancel': `"<strong>${complaintTitle}</strong>" başlıklı şikayeti iptal etmek istediğinizden emin misiniz?`,
            'status': `Şikayet durumunu güncellemek istediğinizden emin misiniz?`
        };
        return messages[type] || 'İşlemi onaylıyor musunuz?';
    }

    /**
     * Modal türüne göre ikon SVG'sini döndürür.
     * 
     * @param {string} type - Modal türü
     * @returns {string} SVG ikonu
     */
    getModalIcon(type) {
        const icons = {
            'withdraw': '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>',
            'cancel': '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
            'status': '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        };
        return icons[type] || icons['status'];
    }

    /**
     * Tüm açık modal'ları kapatır.
     */
    closeAllModals() {
        const modals = document.querySelectorAll('.modal-backdrop');
        
        modals.forEach(modal => {
            // Kapatma animasyonu
            modal.classList.add('opacity-0');
            modal.querySelector('.modal-content')?.classList.add('scale-95');
            
            // Animasyon tamamlandıktan sonra DOM'dan kaldır
            setTimeout(() => {
            modal.remove();
            }, 300);
        });
        
        this.isModalOpen = false;
    }

    /**
     * Kullanıcıdan aksiyon onayı alır.
     * 
     * @param {string} message - Onay mesajı
     * @returns {boolean} Kullanıcı onayı
     */
    confirmAction(message) {
        return confirm(message);
    }

    /**
     * CSRF token'ını DOM'dan alır.
     * 
     * @returns {string} CSRF token değeri
     */
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Bildirim gösterir.
     * 
     * @param {string} message - Bildirim mesajı
     * @param {string} type - Bildirim türü (success, error, warning, info)
     * @param {number} duration - Gösterim süresi (ms)
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        
        // Bildirim türüne göre stil sınıfları
        const typeClasses = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'warning': 'bg-yellow-500 text-white',
            'info': 'bg-blue-500 text-white'
        };
        
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm transform transition-all duration-300 translate-x-full ${typeClasses[type]}`;
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button class="ml-3 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;

        // Bildirimi DOM'a ekle
        document.body.appendChild(notification);

        // Giriş animasyonu
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);
        
        // Otomatik kapatma
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, duration);
    }

    /**
     * Tooltip gösterir.
     * 
     * @param {HTMLElement} element - Tooltip'in bağlı olduğu element
     * @param {string} text - Tooltip metni
     */
    showTooltip(element, text) {
        // Mevcut tooltip'i kaldır
        this.hideTooltip();
        
        const tooltip = document.createElement('div');
        tooltip.className = 'absolute bg-gray-800 text-white text-sm rounded py-1 px-2 z-50 pointer-events-none tooltip';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        // Tooltip pozisyonunu ayarla
        const rect = element.getBoundingClientRect();
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
    }

    /**
     * Tooltip'i gizler.
     */
    hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    /**
     * Otomatik tamamlama işlevini yönetir.
     * 
     * @param {HTMLInputElement} input - Input elementi
     */
    async handleAutoComplete(input) {
        const value = input.value.trim();
        
        if (value.length < 2) {
            this.hideAutoComplete();
            return;
        }
        
        try {
            // API'den öneriler al
            const response = await fetch(`${this.baseUrl}api/autocomplete/?q=${encodeURIComponent(value)}`);
            const suggestions = await response.json();
            
            this.showAutoComplete(input, suggestions);
        } catch (error) {
            console.error('Otomatik tamamlama hatası:', error);
        }
    }

    /**
     * Otomatik tamamlama önerilerini gösterir.
     * 
     * @param {HTMLInputElement} input - Input elementi
     * @param {Array} suggestions - Öneri listesi
     */
    showAutoComplete(input, suggestions) {
        // Mevcut öneri listesini kaldır
        this.hideAutoComplete();
        
        if (!suggestions || suggestions.length === 0) {
            return;
        }
        
        const dropdown = document.createElement('div');
        dropdown.className = 'absolute bg-white border border-gray-300 rounded-md shadow-lg z-50 max-h-48 overflow-y-auto autocomplete-dropdown';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'px-3 py-2 cursor-pointer hover:bg-gray-100';
            item.textContent = suggestion.text;
            item.addEventListener('click', () => {
                input.value = suggestion.value;
                this.hideAutoComplete();
            });
            dropdown.appendChild(item);
        });
        
        // Dropdown pozisyonunu ayarla
        const rect = input.getBoundingClientRect();
        dropdown.style.top = `${rect.bottom}px`;
        dropdown.style.left = `${rect.left}px`;
        dropdown.style.width = `${rect.width}px`;
        
        document.body.appendChild(dropdown);
    }

    /**
     * Otomatik tamamlama dropdown'ını gizler.
     */
    hideAutoComplete() {
        const dropdown = document.querySelector('.autocomplete-dropdown');
        if (dropdown) {
            dropdown.remove();
        }
    }

    /**
     * AJAX ile şikayet durumu günceller.
     * 
     * @param {string} complaintId - Şikayet UUID'si
     * @param {string} newStatus - Yeni durum
     * @param {string} reason - Durum değişiklik sebebi
     * @returns {Promise} AJAX isteği promise'i
     */
    async updateComplaintStatus(complaintId, newStatus, reason = '') {
        try {
            const response = await fetch(`${this.baseUrl}${complaintId}/update_status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    status: newStatus,
                    reason: reason
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Şikayet durumu başarıyla güncellendi.', 'success');
                // Sayfayı yenile veya DOM'u güncelle
                setTimeout(() => {
                location.reload();
                }, 1500);
            } else {
                this.showNotification(result.message || 'Durum güncellenirken bir hata oluştu.', 'error');
            }
            
            return result;
        } catch (error) {
            console.error('Durum güncelleme hatası:', error);
            this.showNotification('Ağ hatası oluştu. Lütfen tekrar deneyin.', 'error');
            throw error;
        }
    }

    /**
     * Şikayet istatistiklerini getirir.
     * 
     * @returns {Promise<Object>} İstatistik verileri
     */
    async getComplaintStats() {
        try {
            const response = await fetch(`${this.baseUrl}api/stats/`);
            const stats = await response.json();
            return stats;
        } catch (error) {
            console.error('İstatistik alma hatası:', error);
            return null;
        }
    }

    /**
     * Form otomatik kaydetme özelliğini başlatır.
     * 
     * @param {string} formSelector - Form CSS seçicisi
     * @param {number} interval - Kaydetme aralığı (ms)
     */
    initAutoSave(formSelector, interval = 30000) {
        const form = document.querySelector(formSelector);
        
        if (!form) {
            return;
        }
        
        // Mevcut interval'i temizle
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        // Yeni interval başlat
        this.autoSaveInterval = setInterval(() => {
            this.autoSave(form);
        }, interval);

        // Sayfa kapatılırken interval'i temizle
        window.addEventListener('beforeunload', () => {
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
            }
        });
    }

    /**
     * Form verilerini otomatik olarak kaydeder.
     * 
     * @param {HTMLFormElement} form - Kaydedilecek form
     */
    async autoSave(form) {
        try {
        const formData = new FormData(form);
        formData.append('auto_save', 'true');

            const response = await fetch(form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });

            if (response.ok) {
                // Başarılı kaydetme göstergesi
                this.showAutoSaveIndicator('success');
            } else {
                this.showAutoSaveIndicator('error');
            }
        } catch (error) {
            console.error('Otomatik kaydetme hatası:', error);
            this.showAutoSaveIndicator('error');
        }
    }

    /**
     * Otomatik kaydetme durumu göstergesini gösterir.
     * 
     * @param {string} status - Kaydetme durumu (success, error)
     */
    showAutoSaveIndicator(status) {
        const indicator = document.querySelector('.auto-save-indicator');
        
        if (!indicator) {
            return;
        }
        
        const messages = {
            'success': 'Otomatik olarak kaydedildi',
            'error': 'Kaydetme hatası'
        };
        
        const colors = {
            'success': 'text-green-600',
            'error': 'text-red-600'
        };
        
        indicator.textContent = messages[status];
        indicator.className = `auto-save-indicator ${colors[status]}`;
        
        // 3 saniye sonra gizle
        setTimeout(() => {
            indicator.textContent = '';
            indicator.className = 'auto-save-indicator';
        }, 3000);
    }
}

// Sayfa yüklendiğinde ComplaintManager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    // Global ComplaintManager instance'ı oluştur
    window.complaintManager = new ComplaintManager();
    
    // Debug için console'a bilgi ver
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('🔧 Solutio 360 Complaint Manager başlatıldı');
        console.log('📋 Mevcut özellikler: Geri çekme, İptal, Silme, Durum güncelleme, Otomatik kaydetme');
    }
});

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComplaintManager;
} 