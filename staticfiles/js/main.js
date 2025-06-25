/**
 * Solutio 360 - Ana JavaScript Dosyası
 * ===================================
 * 
 * Solutio 360 PWA uygulaması için genel JavaScript işlevselliği.
 * Form yönetimi, modal işlemleri, alert sistemi ve utility fonksiyonları.
 * 
 * Bağımlılıklar:
 * - jQuery 3.6+
 * - Select2 4.1+
 * - Tailwind CSS
 * 
 * Özellikler:
 * - AJAX form işleme
 * - Select2 entegrasyonu
 * - Modal yönetimi
 * - Alert/bildirim sistemi
 * - Tarih formatlama
 * - Tablo sıralama
 * - Excel/PDF export
 * 
 * @author Solutio 360 Development Team
 * @version 1.0.0
 */

// Bağımlılık kontrolü - jQuery ve Select2 yüklenmiş mi?
console.log('jQuery:', typeof window.jQuery, 'Select2:', typeof $.fn.select2);

/**
 * DOM hazır olduğunda çalışacak kodlar.
 * Select2 dropdown'larını başlatır.
 */
$(function() {
    // jQuery ve Select2 kontrolü
    if (window.jQuery && $.fn.select2) {
        // Tüm select elementleri için Select2 aktif et
        $('#id_category, #id_priority, #id_status, #id_tags, #id_complained_institutions, #id_complained_units, #id_complained_subunits, #id_complained_people, .select2').select2({
            width: '100%',                    // Tam genişlik
            placeholder: 'Seçiniz veya yazınız',  // Placeholder metni
            allowClear: true,                 // Temizleme butonu
            tags: true                        // Yeni etiket ekleme izni
        });
    }
});

/**
 * Utility Functions - Yardımcı Fonksiyonlar
 * =========================================
 */

/**
 * Tarih string'ini Türkçe formatta formatlar.
 * 
 * @param {string} dateString - ISO tarih string'i
 * @returns {string} Formatlanmış tarih (örn: "15 Ocak 2024")
 */
const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('tr-TR', options);
};

/**
 * Tarih ve saat string'ini Türkçe formatta formatlar.
 * 
 * @param {string} dateString - ISO tarih string'i
 * @returns {string} Formatlanmış tarih ve saat (örn: "15 Ocak 2024 14:30")
 */
const formatDateTime = (dateString) => {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('tr-TR', options);
};

/**
 * Form İşleme Fonksiyonları
 * =========================
 */

/**
 * AJAX ile form gönderimi işler.
 * Loading state, hata yönetimi ve başarı callback'i içerir.
 * 
 * @param {HTMLFormElement} formElement - Gönderilecek form elementi
 * @param {Function} successCallback - Başarılı gönderim sonrası çalışacak fonksiyon
 */
const handleFormSubmit = async (formElement, successCallback) => {
    // Form verilerini hazırla
    const formData = new FormData(formElement);
    const submitButton = formElement.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    
    try {
        // Loading state - buton devre dışı ve loading göster
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner"></span> İşleniyor...';
        
        // AJAX isteği gönder
        const response = await fetch(formElement.action, {
            method: formElement.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'  // Django AJAX kontrolü için
            }
        });
        
        // JSON response'u parse et
        const data = await response.json();
        
        if (response.ok) {
            // Başarılı işlem
            if (successCallback) {
                successCallback(data);
            }
            showAlert('success', data.message || 'İşlem başarıyla tamamlandı.');
        } else {
            // Hata durumu
            showAlert('error', data.message || 'Bir hata oluştu.');
            
            // Form validation hatalarını göster
            if (data.errors) {
                Object.keys(data.errors).forEach(field => {
                    const input = formElement.querySelector(`[name="${field}"]`);
                    if (input) {
                        // Input'u hata rengine çevir
                        input.classList.add('border-red-500');
                        
                        // Hata mesajı ekle
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'form-error text-red-500 text-sm mt-1';
                        errorDiv.textContent = data.errors[field].join(', ');
                        input.parentNode.appendChild(errorDiv);
                    }
                });
            }
        }
    } catch (error) {
        // Network veya parse hatası
        console.error('Form gönderim hatası:', error);
        showAlert('error', 'Bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
        // Loading state'i kaldır
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
};

/**
 * Alert/Bildirim Sistemi
 * ======================
 */

/**
 * Kullanıcıya alert/bildirim gösterir.
 * Otomatik olarak 5 saniye sonra kaybolur.
 * 
 * @param {string} type - Alert türü (success, error, warning, info)
 * @param {string} message - Gösterilecek mesaj
 */
const showAlert = (type, message) => {
    // Alert container oluştur
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} fixed top-4 right-4 z-50 max-w-sm bg-white border rounded-lg shadow-lg p-4`;
    
    // Alert içeriğini ayarla
    alertContainer.innerHTML = `
        <div class="flex items-center">
            <span class="mr-3">${getAlertIcon(type)}</span>
            <p class="text-sm text-gray-800">${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-gray-400 hover:text-gray-600">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    // DOM'a ekle
    document.body.appendChild(alertContainer);
    
    // Giriş animasyonu
    setTimeout(() => {
        alertContainer.classList.add('animate-slide-in');
    }, 10);
    
    // 5 saniye sonra otomatik kaldır
    setTimeout(() => {
        alertContainer.classList.add('animate-slide-out');
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.remove();
            }
        }, 300);
    }, 5000);
};

/**
 * Alert türüne göre ikon SVG'si döndürür.
 * 
 * @param {string} type - Alert türü
 * @returns {string} SVG ikon HTML'i
 */
const getAlertIcon = (type) => {
    const icons = {
        success: '<svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
        error: '<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
        warning: '<svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        info: '<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };
    return icons[type] || icons.info;
};

/**
 * Modal Yönetimi
 * ==============
 */

/**
 * Modal dialog'u gösterir.
 * 
 * @param {string} modalId - Modal element ID'si
 */
const showModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';  // Arka plan scroll'unu engelle
        
        // Modal animasyonu
        setTimeout(() => {
            modal.classList.add('modal-show');
        }, 10);
    }
};

/**
 * Modal dialog'u gizler.
 * 
 * @param {string} modalId - Modal element ID'si
 */
const hideModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('modal-show');
        
        // Animasyon tamamlandıktan sonra gizle
        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';  // Scroll'u geri aç
        }, 300);
    }
};

/**
 * Filtreleme ve Sıralama
 * ======================
 */

/**
 * Filter değişikliğinde formu otomatik gönderir.
 * 
 * @param {HTMLFormElement} formElement - Filter form elementi
 */
const handleFilterChange = (formElement) => {
    // Form'u otomatik gönder
    formElement.submit();
};

/**
 * Tablo sıralaması yapar (client-side).
 * 
 * @param {HTMLTableElement} tableElement - Sıralanacak tablo
 * @param {string} column - Sıralama yapılacak kolon adı
 */
const handleTableSort = (tableElement, column) => {
    // Mevcut sıralama yönünü tersine çevir
    const currentDirection = tableElement.dataset.sortDirection === 'asc' ? 'desc' : 'asc';
    tableElement.dataset.sortColumn = column;
    tableElement.dataset.sortDirection = currentDirection;
    
    // Tablo satırlarını al ve sırala
    const rows = Array.from(tableElement.querySelectorAll('tbody tr'));
    const sortedRows = rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-column="${column}"]`).textContent.trim();
        const bValue = b.querySelector(`td[data-column="${column}"]`).textContent.trim();
        
        // Türkçe karakter desteği ile karşılaştırma
        if (currentDirection === 'asc') {
            return aValue.localeCompare(bValue, 'tr');
        } else {
            return bValue.localeCompare(aValue, 'tr');
        }
    });
    
    // Sıralanmış satırları tabloya geri ekle
    const tbody = tableElement.querySelector('tbody');
    tbody.innerHTML = '';
    sortedRows.forEach(row => tbody.appendChild(row));
    
    // Sıralama göstergesini güncelle
    updateSortIndicators(tableElement, column, currentDirection);
};

/**
 * Tablo başlıklarındaki sıralama göstergelerini günceller.
 * 
 * @param {HTMLTableElement} tableElement - Tablo elementi
 * @param {string} activeColumn - Aktif sıralama kolonu
 * @param {string} direction - Sıralama yönü (asc/desc)
 */
const updateSortIndicators = (tableElement, activeColumn, direction) => {
    // Tüm sıralama göstergelerini temizle
    tableElement.querySelectorAll('th[data-sort]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Aktif kolona sıralama göstergesini ekle
    const activeHeader = tableElement.querySelector(`th[data-sort="${activeColumn}"]`);
    if (activeHeader) {
        activeHeader.classList.add(`sort-${direction}`);
    }
};

/**
 * Export İşlemleri
 * ================
 */

/**
 * Excel dosyası olarak export eder.
 * 
 * @param {string} url - Export endpoint URL'i
 */
const exportToExcel = async (url) => {
    try {
        // Loading göster
        showAlert('info', 'Excel dosyası hazırlanıyor...');
        
        // Export isteği gönder
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error('Export başarısız');
        }
        
        // Blob olarak al ve indir
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `rapor_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        
        // Temizlik
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();
        
        showAlert('success', 'Excel dosyası başarıyla indirildi.');
    } catch (error) {
        console.error('Excel export hatası:', error);
        showAlert('error', 'Excel dosyası oluşturulurken bir hata oluştu.');
    }
};

/**
 * PDF dosyası olarak export eder.
 * 
 * @param {string} url - Export endpoint URL'i
 */
const exportToPDF = async (url) => {
    try {
        // Loading göster
        showAlert('info', 'PDF dosyası hazırlanıyor...');
        
        // Export isteği gönder
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error('Export başarısız');
        }
        
        // Blob olarak al ve indir
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `rapor_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        
        // Temizlik
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();
        
        showAlert('success', 'PDF dosyası başarıyla indirildi.');
    } catch (error) {
        console.error('PDF export hatası:', error);
        showAlert('error', 'PDF dosyası oluşturulurken bir hata oluştu.');
    }
};

/**
 * Başlatma ve Event Listener'lar
 * ===============================
 */

/**
 * DOM yüklendiğinde çalışacak başlatma kodları.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Main] Solutio 360 Main.js başlatılıyor...');
    
    // AJAX form handling - data-ajax="true" olan formlar
    document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Form hatalarını temizle
            form.querySelectorAll('.form-error').forEach(error => error.remove());
            form.querySelectorAll('.border-red-500').forEach(input => {
                input.classList.remove('border-red-500');
            });
            
            // Form'u AJAX ile gönder
            handleFormSubmit(form);
        });
    });
    
    // Filter handling - data-filter="true" olan select'ler
    document.querySelectorAll('select[data-filter="true"]').forEach(select => {
        select.addEventListener('change', () => {
            handleFilterChange(select.closest('form'));
        });
    });
    
    // Table sorting - data-sort attribute'u olan başlıklar
    document.querySelectorAll('th[data-sort]').forEach(header => {
        header.addEventListener('click', () => {
            const table = header.closest('table');
            const column = header.dataset.sort;
            handleTableSort(table, column);
        });
        
        // Cursor pointer ekle
        header.style.cursor = 'pointer';
    });
    
    // Modal handling - data-modal attribute'u olan butonlar
    document.querySelectorAll('[data-modal]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = button.dataset.modal;
            showModal(modalId);
        });
    });
    
    // Modal kapatma - .modal-close sınıfı olan elementler
    document.querySelectorAll('.modal-close').forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = closeBtn.closest('.modal');
            if (modal) {
                hideModal(modal.id);
            }
        });
    });
    
    // Modal backdrop tıklama ile kapatma
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal(modal.id);
            }
        });
    });
    
    // ESC tuşu ile modal kapatma
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal:not(.hidden)').forEach(modal => {
                hideModal(modal.id);
            });
        }
    });
    
    // Export butonları
    document.querySelectorAll('[data-export="excel"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            exportToExcel(btn.href || btn.dataset.url);
        });
    });
    
    document.querySelectorAll('[data-export="pdf"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            exportToPDF(btn.href || btn.dataset.url);
        });
    });
    
    console.log('[Main] Solutio 360 Main.js başlatıldı');
}); 