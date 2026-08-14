/* Expenses Page Script for CRUD table management & multi-criteria filtering */

document.addEventListener('DOMContentLoaded', () => {
    if (window.__expensePageHandlersBound) return;
    window.__expensePageHandlersBound = true;

    initExpenseTableActions();
    loadExpenses();
    initExpenseFilters();
    initEditExpenseForm();
});

let allExpensesCache = [];

function initExpenseTableActions() {
    const tableBody = document.getElementById('expensesTableBody');
    if (!tableBody) return;

    tableBody.addEventListener('click', (event) => {
        const editButton = event.target.closest('[data-action="edit-expense"]');
        if (editButton) {
            event.preventDefault();
            openEditExpenseModal(editButton.dataset.expenseId);
            return;
        }

        const deleteButton = event.target.closest('[data-action="delete-expense"]');
        if (deleteButton) {
            event.preventDefault();
            deleteExpenseItem(deleteButton.dataset.expenseId);
        }
    });
}

async function loadExpenses() {
    const search = document.getElementById('filterSearch').value;
    const category = document.getElementById('filterCategory').value;
    const payment = document.getElementById('filterPayment').value;
    const startDate = document.getElementById('filterStartDate').value;
    const endDate = document.getElementById('filterEndDate').value;

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    if (payment) params.append('payment_method', payment);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    try {
        const data = await fetchAPI(`/api/expenses?${params.toString()}`);
        allExpensesCache = data.expenses;

        document.getElementById('expenseResultCounter').textContent = `Showing ${data.count} expenses`;
        document.getElementById('expenseFilterTotal').textContent = `Total: ₹${data.total_amount.toLocaleString('en-IN')}`;

        renderExpensesTable(data.expenses);
    } catch (err) {
        showToast(err.message, 'danger');
    }
}

function initExpenseFilters() {
    const inputs = ['filterSearch', 'filterCategory', 'filterPayment', 'filterStartDate', 'filterEndDate'];
    inputs.forEach(id => {
        const elem = document.getElementById(id);
        if (elem) {
            elem.addEventListener('change', loadExpenses);
            if (id === 'filterSearch') {
                let t = null;
                elem.addEventListener('input', () => {
                    clearTimeout(t);
                    t = setTimeout(loadExpenses, 300);
                });
            }
        }
    });

    document.getElementById('resetFiltersBtn').addEventListener('click', () => {
        document.getElementById('filterSearch').value = '';
        document.getElementById('filterCategory').value = 'All';
        document.getElementById('filterPayment').value = 'All';
        document.getElementById('filterStartDate').value = '';
        document.getElementById('filterEndDate').value = '';
        loadExpenses();
    });
}

function renderExpensesTable(expenses) {
    const tbody = document.getElementById('expensesTableBody');
    if (!expenses || expenses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-5"><i class="bi bi-inbox fs-2 d-block mb-2"></i>No expenses matched your filter criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = expenses.map(e => {
        let flags = '';
        if (e.is_recurring) flags += '<span class="badge bg-info-subtle text-info me-1">Recurring</span>';
        if (e.is_anomaly) flags += '<span class="badge bg-warning-subtle text-warning me-1"><i class="bi bi-exclamation-triangle"></i> Outlier</span>';
        if (e.predicted_category) flags += `<span class="badge bg-primary-subtle text-primary" title="Confidence: ${e.prediction_confidence ? Math.round(e.prediction_confidence * 100) : 0}%">ML: ${e.predicted_category}</span>`;

        return `
            <tr>
                <td class="ps-3 text-nowrap">${e.date}</td>
                <td class="fw-semibold expense-desc-cell">
                    ${e.description}
                    ${e.notes ? `<small class="text-muted d-block font-monospace" style="font-size:0.75rem;">${e.notes}</small>` : ''}
                </td>
                <td><span class="badge bg-secondary-subtle text-secondary">${e.category}</span></td>
                <td>${e.payment_method}</td>
                <td>${flags || '<span class="text-muted small">-</span>'}</td>
                <td class="text-end fw-bold">₹${e.amount.toLocaleString('en-IN')}</td>
                <td class="text-end pe-3">
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-secondary" data-action="edit-expense" data-expense-id="${e.id}" title="Edit">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger" data-action="delete-expense" data-expense-id="${e.id}" title="Delete">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}

function openEditExpenseModal(id) {
    const exp = allExpensesCache.find(e => Number(e.id) === Number(id));
    if (!exp) {
        console.error('Expense not found in cache for ID:', id);
        showToast('Expense record not found in active view.', 'warning');
        return;
    }

    document.getElementById('editExpenseId').value = exp.id;
    document.getElementById('editDescription').value = exp.description;
    document.getElementById('editAmount').value = exp.amount;
    document.getElementById('editDate').value = exp.date;
    document.getElementById('editCategory').value = exp.category;
    document.getElementById('editPayment').value = exp.payment_method;
    document.getElementById('editRecurring').checked = exp.is_recurring;
    document.getElementById('editNotes').value = exp.notes || '';

    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        console.error('Bootstrap 5 JavaScript is unavailable. Edit modal cannot be opened.');
        showToast('Bootstrap is unavailable. Please refresh the page.', 'danger');
        return;
    }

    const modalElem = document.getElementById('editExpenseModal');
    if (modalElem) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalElem);
        modal.show();
    }
}

function initEditExpenseForm() {
    const form = document.getElementById('editExpenseForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('editExpenseId').value;
        const payload = {
            description: document.getElementById('editDescription').value,
            amount: parseFloat(document.getElementById('editAmount').value),
            date: document.getElementById('editDate').value,
            category: document.getElementById('editCategory').value,
            payment_method: document.getElementById('editPayment').value,
            is_recurring: document.getElementById('editRecurring').checked,
            notes: document.getElementById('editNotes').value
        };

        try {
            const res = await fetchAPI(`/api/expenses/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            if (res.success) {
                showToast('Expense updated successfully!', 'success');
                const modalElem = document.getElementById('editExpenseModal');
                if (modalElem) {
                    const modal = bootstrap.Modal.getInstance(modalElem) || bootstrap.Modal.getOrCreateInstance(modalElem);
                    modal.hide();
                }

                loadExpenses();
            }
        } catch (err) {
            showToast(err.message, 'danger');
        }
    });
}

async function deleteExpenseItem(id) {
    if (!confirm('Are you sure you want to delete this expense record?')) return;

    try {
        const res = await fetchAPI(`/api/expenses/${id}`, { method: 'DELETE' });
        if (res.success) {
            showToast('Expense deleted successfully.', 'success');
            loadExpenses();
        }
    } catch (err) {
        showToast(err.message, 'danger');
    }
}

// Explicitly attach window handlers for inline HTML event attributes
window.openEditExpenseModal = openEditExpenseModal;
window.deleteExpenseItem = deleteExpenseItem;

