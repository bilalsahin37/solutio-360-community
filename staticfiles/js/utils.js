/**
 * Utility functions for Solutio 360
 * Genel yardımcı fonksiyonlar
 */

// DOM yüklendikten sonra çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    initUtils();
});

/**
 * Utility fonksiyonlarını başlat
 */
function initUtils() {
    setupToastNotifications();
    setupFormValidations();
    setupTooltips();
    setupAsyncLinks();
}

/**
 * Toast bildirim sistemi
 */
function setupToastNotifications() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
}

/**
 * Toast bildirimi göster
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type} bg-white dark:bg-gray-800 border-l-4 p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full opacity-0`;
    
    const colors = {
        success: 'border-green-500 text-green-700 dark:text-green-400',
        error: 'border-red-500 text-red-700 dark:text-red-400',
        warning: 'border-yellow-500 text-yellow-700 dark:text-yellow-400',
        info: 'border-blue-500 text-blue-700 dark:text-blue-400'
    };
    
    toast.className += ` ${colors[type] || colors.info}`;
    
    toast.innerHTML = `
        <div class="flex items-center">
            <div class="flex-1">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <button type="button" class="ml-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                <span class="sr-only">Kapat</span>
                <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    }, 100);
    
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Form validasyonlarını ayarla
 */
function setupFormValidations() {
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.tagName === 'FORM') {
            if (!validateForm(form)) {
                e.preventDefault();
                return false;
            }
        }
    });
}

/**
 * Form validasyonu yap
 */
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Tek bir alanı validate et
 */
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let message = '';
    
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'Bu alan zorunludur.';
    } else if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Geçerli bir email adresi giriniz.';
        }
    }
    
    showFieldError(field, isValid ? null : message);
    return isValid;
}

/**
 * Alan hata mesajını göster/gizle
 */
function showFieldError(field, message) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    if (message) {
        field.classList.add('border-red-500', 'focus:border-red-500');
        field.classList.remove('border-gray-300', 'focus:border-blue-500');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-red-600 text-sm mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    } else {
        field.classList.remove('border-red-500', 'focus:border-red-500');
        field.classList.add('border-gray-300', 'focus:border-blue-500');
    }
}

/**
 * Tooltip'leri ayarla
 */
function setupTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Tooltip göster
 */
function showTooltip(e) {
    const element = e.target;
    const text = element.getAttribute('data-tooltip');
    
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.id = 'tooltip';
    tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

/**
 * Tooltip gizle
 */
function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Async link'leri ayarla
 */
function setupAsyncLinks() {
    document.addEventListener('click', function(e) {
        const link = e.target.closest('[data-async]');
        if (link) {
            e.preventDefault();
            handleAsyncLink(link);
        }
    });
}

/**
 * Async link'i işle
 */
function handleAsyncLink(link) {
    const url = link.href || link.getAttribute('data-url');
    const method = link.getAttribute('data-method') || 'GET';
    const confirm = link.getAttribute('data-confirm');
    
    if (confirm && !window.confirm(confirm)) {
        return;
    }
    
    showLoading();
    
    fetch(url, {
        method: method,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.status === 'success') {
            showToast(data.message || 'İşlem başarılı', 'success');
            if (data.reload) {
                window.location.reload();
            }
        } else {
            showToast(data.message || 'Bir hata oluştu', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Bağlantı hatası', 'error');
        console.error('Async link error:', error);
    });
}

/**
 * Loading spinner göster
 */
function showLoading() {
    const loading = document.getElementById('global-loading');
    if (loading) {
        loading.classList.remove('hidden');
    }
}

/**
 * Loading spinner gizle
 */
function hideLoading() {
    const loading = document.getElementById('global-loading');
    if (loading) {
        loading.classList.add('hidden');
    }
}

/**
 * CSRF token'ını al
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
        return meta.getAttribute('content');
    }
    
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    if (cookie) {
        return cookie.split('=')[1];
    }
    
    return '';
}

/**
 * URL parametrelerini al
 */
function getUrlParams() {
    const params = {};
    const searchParams = new URLSearchParams(window.location.search);
    
    for (const [key, value] of searchParams) {
        params[key] = value;
    }
    
    return params;
}

/**
 * Tarih formatla
 */
function formatDate(date, format = 'tr-TR') {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    
    return date.toLocaleDateString(format);
}

/**
 * Sayıyı formatla
 */
function formatNumber(number) {
    return new Intl.NumberFormat('tr-TR').format(number);
}

// Global fonksiyonları window objesine ekle
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.getCsrfToken = getCsrfToken;
window.getUrlParams = getUrlParams;
window.formatDate = formatDate;
window.formatNumber = formatNumber; 
