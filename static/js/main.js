/* Global Application JavaScript Helpers */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebarToggle();
    bindOpenModalButtons();
    initQuickAddExpense();
});

function bindOpenModalButtons() {
    document.querySelectorAll('[data-open-modal]').forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const modalId = button.getAttribute('data-open-modal');
            if (!modalId) return;
            openBootstrapModal(modalId);
        });
    });
}

function openBootstrapModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
        console.error(`Bootstrap modal target not found: #${modalId}`);
        return null;
    }

    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        console.error('Bootstrap 5 JavaScript is unavailable. Modal cannot be opened.');
        return null;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.show();
    return modal;
}

function closeBootstrapModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;

    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        console.error('Bootstrap 5 JavaScript is unavailable. Modal cannot be closed.');
        return;
    }

    const modal = bootstrap.Modal.getInstance(modalElement) || bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.hide();
}

// Generic Fetch Wrapper
async function fetchAPI(url, options = {}) {
    try {
        // Prevent browser caching to ensure real-time UI updates
        if (!options.method || options.method.toUpperCase() === 'GET') {
            options.cache = 'no-store';
            const separator = url.includes('?') ? '&' : '?';
            url = `${url}${separator}_t=${Date.now()}`;
        } else if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
            // Attach CSRF token header for state-modifying requests
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            if (csrfToken) {
                options.headers = {
                    ...options.headers,
                    'X-CSRFToken': csrfToken
                };
            }
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            let errorMessage = `Request failed with status ${response.status}`;

            try {
                const errData = await response.json();
                if (errData && errData.message) {
                    errorMessage = errData.message;
                } else if (errData && errData.error) {
                    errorMessage = errData.error;
                }
            } catch (_) {
                try {
                    const text = await response.text();
                    if (text) errorMessage = text;
                } catch (_) {
                    // Ignore and keep the fallback error.
                }
            }

            throw new Error(errorMessage);
        }
        return await response.json();
    } catch (err) {
        console.error(`API Error [${url}]:`, err);
        throw err;
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toastElem = document.getElementById('appToast');
    const msgElem = document.getElementById('toastMessage');
    const iconElem = document.getElementById('toastIcon');
    if (!toastElem || !msgElem || !iconElem) return;

    if (typeof bootstrap === 'undefined' || !bootstrap.Toast) {
        console.error('Bootstrap 5 toast is unavailable. Notification:', message);
        return;
    }

    msgElem.textContent = message;

    // Set Bootstrap alert color class
    toastElem.className = `toast align-items-center text-white border-0 shadow bg-${type}`;

    // Set Icon
    if (type === 'success') iconElem.className = 'bi bi-check-circle-fill fs-5';
    else if (type === 'danger') iconElem.className = 'bi bi-exclamation-triangle-fill fs-5';
    else if (type === 'warning') iconElem.className = 'bi bi-exclamation-circle-fill fs-5';
    else iconElem.className = 'bi bi-info-circle-fill fs-5';

    const toast = new bootstrap.Toast(toastElem, { delay: 4000 });
    toast.show();
}

// Theme Switcher (Light / Dark)
function initTheme() {
    const themeBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    if (!themeBtn) return;

    const savedTheme = localStorage.getItem('app-theme') || 'light';
    setTheme(savedTheme);

    themeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    function setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('app-theme', theme);
        if (theme === 'dark') {
            if (themeIcon) themeIcon.className = 'bi bi-sun';
            if (themeText) themeText.textContent = 'Light Mode';
        } else {
            if (themeIcon) themeIcon.className = 'bi bi-moon-stars';
            if (themeText) themeText.textContent = 'Dark Mode';
        }
    }
}

// Sidebar toggle for mobile
function initSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => sidebar.classList.add('show'));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => sidebar.classList.remove('show'));
    }
}

// Real-Time ML Category Auto-Suggest & Quick Add Expense Modal Form
function initQuickAddExpense() {
    const descInput = document.getElementById('quickDescription');
    const dateInput = document.getElementById('quickDate');
    const form = document.getElementById('quickAddExpenseForm');

    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    if (descInput) {
        let timer = null;
        descInput.addEventListener('input', () => {
            clearTimeout(timer);
            const val = descInput.value.trim();
            if (val.length < 3) {
                document.getElementById('mlSuggestionBadge').classList.add('d-none');
                return;
            }

            timer = setTimeout(async () => {
                try {
                    const res = await fetchAPI('/api/expenses/categorize-preview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ description: val })
                    });
                    
                    if (res.predicted_category) {
                        document.getElementById('suggestedCatText').textContent = res.predicted_category;
                        document.getElementById('suggestedConfText').textContent = `${Math.round(res.confidence * 100)}%`;
                        document.getElementById('mlSuggestionBadge').classList.remove('d-none');
                    }
                } catch (e) {
                    console.log('Preview fail:', e);
                }
            }, 300);
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                description: document.getElementById('quickDescription').value,
                amount: parseFloat(document.getElementById('quickAmount').value),
                date: document.getElementById('quickDate').value,
                category: document.getElementById('quickCategory').value,
                payment_method: document.getElementById('quickPayment').value,
                is_recurring: document.getElementById('quickRecurring').checked,
                notes: document.getElementById('quickNotes').value
            };

            try {
                const res = await fetchAPI('/api/expenses', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.success) {
                    showToast(`Expense saved! Category: ${res.expense.category}`, 'success');
                    form.reset();
                    document.getElementById('quickDate').value = new Date().toISOString().split('T')[0];
                    document.getElementById('mlSuggestionBadge').classList.add('d-none');
                    
                    closeBootstrapModal('quickAddModal');

                    // Refresh current page context if dashboard or expenses function available
                    if (typeof loadDashboardData === 'function') loadDashboardData();
                    if (typeof loadExpenses === 'function') loadExpenses();
                }
            } catch (err) {
                showToast(err.message, 'danger');
            }
        });
    }
}
