// ===================================
// UTILITY FUNCTIONS
// ===================================

/**
 * Make API call with error handling
 */
async function apiCall(url, method = 'GET', data = null) {
     const options = {
          method: method,
          headers: {
               'Content-Type': 'application/json'
          }
     };

     if (data && method !== 'GET') {
          options.body = JSON.stringify(data);
     }

     try {
          const response = await fetch(url, options);
          const result = await response.json();
          return result;
     } catch (error) {
          console.error('API Error:', error);
          return { success: false, error: error.message };
     }
}

/**
 * Show popup message
 */
function showPopup(message, type = 'info') {
     const popup = document.createElement('div');
     popup.className = `popup popup-${type}`;
     popup.textContent = message;
     popup.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;

     document.body.appendChild(popup);

     setTimeout(() => {
          popup.style.animation = 'slideOut 0.3s ease-out';
          setTimeout(() => popup.remove(), 300);
     }, 3000);
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
     if (!dateString) return 'N/A';
     const date = new Date(dateString);
     return date.toLocaleDateString('en-IN', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
     });
}

/**
 * Format currency (Indian Rupees)
 */
function formatCurrency(amount) {
     return new Intl.NumberFormat('en-IN', {
          style: 'currency',
          currency: 'INR',
          minimumFractionDigits: 0
     }).format(amount);
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
     const statusClass = `status-${status.toLowerCase()}`;
     return `<span class="status-badge ${statusClass}">${status}</span>`;
}

/**
 * Get rating stars HTML
 */
function getRatingStars(rating) {
     if (!rating) return 'N/A';
     const fullStars = Math.floor(rating);
     const halfStar = rating % 1 >= 0.5 ? 1 : 0;
     const emptyStars = 5 - fullStars - halfStar;

     let stars = '⭐'.repeat(fullStars);
     if (halfStar) stars += '⯨';
     stars += '☆'.repeat(emptyStars);

     return `${stars} (${rating.toFixed(1)})`;
}

/**
 * Validate email format
 */
function validateEmail(email) {
     const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
     return re.test(email);
}

/**
 * Validate phone number (Indian format)
 */
function validatePhone(phone) {
     const re = /^[6-9]\d{9}$/;
     return re.test(phone);
}

/**
 * Show loading spinner
 */
function showLoading(containerId) {
     const container = document.getElementById(containerId);
     if (container) {
          container.innerHTML = `
            <div style="text-align: center; padding: 50px;">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        `;
     }
}

/**
 * Confirm action dialog
 */
function confirmAction(message) {
     return confirm(message);
}

/**
 * Clear form fields
 */
function clearForm(formId) {
     const form = document.getElementById(formId);
     if (form) {
          form.reset();
     }
}

/**
 * Enable/disable form submit button
 */
function toggleSubmitButton(buttonId, disabled = true) {
     const button = document.getElementById(buttonId);
     if (button) {
          button.disabled = disabled;
          button.style.opacity = disabled ? '0.6' : '1';
          button.style.cursor = disabled ? 'not-allowed' : 'pointer';
     }
}

// ===================================
// ADD ANIMATIONS
// ===================================

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// ===================================
// EXPORT FUNCTIONS (if using modules)
// ===================================

// Uncomment if using ES6 modules
// export { apiCall, showPopup, formatDate, formatCurrency, getStatusBadge, getRatingStars };
