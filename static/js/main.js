/**
 * AI Travel Planner - Main JavaScript File
 */

// DOM Elements
const chatbotToggle = document.getElementById('chatbotToggle');
const chatbotContainer = document.getElementById('chatbotContainer');
const chatbotClose = document.getElementById('chatbotClose');
const chatbotMessages = document.getElementById('chatbotMessages');
const chatbotInput = document.getElementById('chatbotInput');
const chatbotSend = document.getElementById('chatbotSend');

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initChatbot();
    initAnimations();
});

/**
 * Chatbot Functionality
 */
function initChatbot() {
    if (!chatbotToggle) return;
    
    // Toggle chatbot
    chatbotToggle.addEventListener('click', function() {
        chatbotContainer.classList.toggle('active');
    });
    
    // Close chatbot
    if (chatbotClose) {
        chatbotClose.addEventListener('click', function() {
            chatbotContainer.classList.remove('active');
        });
    }
    
    // Send message on button click
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendMessage);
    }
    
    // Send message on Enter key
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

/**
 * Send message to chatbot
 */
function sendMessage() {
    const message = chatbotInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    chatbotInput.value = '';
    
    // Show loading indicator
    const loadingId = 'loading-' + Date.now();
    addLoadingMessage(loadingId);
    
    // Send to server
    fetch('/chatbot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        removeLoadingMessage(loadingId);
        // Add bot response
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        removeLoadingMessage(loadingId);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    });
}

/**
 * Add message to chat
 */
function addMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
    messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    chatbotMessages.appendChild(messageDiv);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

/**
 * Add loading message
 */
function addLoadingMessage(id) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = id;
    loadingDiv.classList.add('message', 'bot-message');
    loadingDiv.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Typing...';
    chatbotMessages.appendChild(loadingDiv);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

/**
 * Remove loading message
 */
function removeLoadingMessage(id) {
    const loadingDiv = document.getElementById(id);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Initialize animations
 */
function initAnimations() {
    // Add fade-in animation to elements
    const animatedElements = document.querySelectorAll('.card, .feature-card, .destination-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, {
        threshold: 0.1
    });
    
    animatedElements.forEach(el => observer.observe(el));
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('main');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0
    }).format(amount);
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Smooth scroll to element
 */
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        });
    } else {
        // Fallback
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Copied to clipboard!', 'success');
    }
}

/**
 * Validate email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Get URL parameters
 */
function getURLParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    for (const [key, value] of params) {
        result[key] = value;
    }
    return result;
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize popovers
 */
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Handle form validation
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Reset form
 */
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        form.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
            el.classList.remove('is-invalid', 'is-valid');
        });
    }
}

// Export functions for global use
window.AITravelPlanner = {
    showNotification,
    formatCurrency,
    debounce,
    smoothScrollTo,
    copyToClipboard,
    validateEmail,
    getURLParams,
    validateForm,
    resetForm
};
