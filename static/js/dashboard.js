/* Dashboard Charts & Real-Time Metric Updates using Chart.js */

let trendChart = null;
let categoryChart = null;
let barChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});

async function loadDashboardData() {
    try {
        const data = await fetchAPI('/api/dashboard');
        const summary = data.summary;
        const symbol = summary.currency_symbol || '₹';

        // 1. Update Metrics Cards
        document.getElementById('dashTotalSpending').textContent = `${symbol}${summary.total_spending_this_month.toLocaleString('en-IN')}`;
        document.getElementById('dashMonthlyBudget').textContent = `${symbol}${summary.monthly_budget.toLocaleString('en-IN')}`;
        document.getElementById('dashRemainingBudget').textContent = `${symbol}${summary.remaining_budget.toLocaleString('en-IN')}`;
        document.getElementById('dashAvgDaily').textContent = `${symbol}${summary.avg_daily_spending.toLocaleString('en-IN')}`;
        document.getElementById('dashTransactionCount').textContent = `${summary.transaction_count} transactions recorded`;
        document.getElementById('dashHighestCat').textContent = `${summary.highest_spending_category} (${symbol}${summary.highest_category_amount.toLocaleString('en-IN')})`;

        // Remaining Budget Progress Bar
        const pctUsed = Math.min((summary.total_spending_this_month / summary.monthly_budget) * 100, 100);
        const remBar = document.getElementById('dashRemainingProgressBar');
        remBar.style.width = `${pctUsed}%`;
        if (pctUsed >= 100) remBar.className = 'progress-bar bg-danger';
        else if (pctUsed >= 80) remBar.className = 'progress-bar bg-warning';
        else remBar.className = 'progress-bar bg-success';

        // Spending Change % Badge
        const changeElem = document.getElementById('dashSpendingChangePct');
        if (summary.spending_change_pct > 0) {
            changeElem.className = 'fw-semibold me-1 text-danger';
            changeElem.innerHTML = `<i class="bi bi-arrow-up-right"></i> +${summary.spending_change_pct}%`;
        } else if (summary.spending_change_pct < 0) {
            changeElem.className = 'fw-semibold me-1 text-success';
            changeElem.innerHTML = `<i class="bi bi-arrow-down-right"></i> ${summary.spending_change_pct}%`;
        } else {
            changeElem.className = 'fw-semibold me-1 text-muted';
            changeElem.textContent = '0%';
        }

        // 2. Render Charts
        renderTrendLineChart(data.daily_trend.labels, data.daily_trend.values, symbol);
        renderCategoryDoughnutChart(data.category_breakdown, symbol);
        renderMonthlyBarChart(data.monthly_comparison, symbol);

        // 3. Update Forecast & Anomalies Teaser
        const fc = data.forecast;
        document.getElementById('dashPredictedTotal').textContent = `${symbol}${fc.predicted_total_spending.toLocaleString('en-IN')}`;
        document.getElementById('dashPredictionSummary').textContent = fc.prediction_summary;
        const statusBadge = document.getElementById('forecastStatusBadge');
        if (fc.will_exceed_budget) {
            statusBadge.className = 'badge bg-danger-subtle text-danger fw-bold';
            statusBadge.textContent = 'Over Budget Risk';
        } else {
            statusBadge.className = 'badge bg-success-subtle text-success fw-bold';
            statusBadge.textContent = 'Within Target';
        }

        const anomalyWidget = document.getElementById('anomalyWidget');
        if (data.unusual_expenses && data.unusual_expenses.length > 0) {
            const first = data.unusual_expenses[0];
            document.getElementById('anomalyWidgetText').textContent = `${symbol}${first.amount.toLocaleString('en-IN')} on ${first.description} - ${first.anomaly_reason || 'Outlier detected'}`;
            anomalyWidget.classList.remove('d-none');
        } else {
            anomalyWidget.className = 'p-3 bg-success-subtle border border-success-subtle rounded-3';
            anomalyWidget.innerHTML = `<div class="d-flex align-items-center gap-2 mb-0"><i class="bi bi-shield-check text-success fs-5"></i><span class="fw-bold text-success">No unusual expenses detected this month.</span></div>`;
        }

        // 4. Render Insights Teaser
        renderInsightsWidget(data.insights);

        // 5. Render Recent Transactions Table
        renderRecentTransactionsTable(data.recent_transactions, symbol);

    } catch (err) {
        showToast(`Dashboard error: ${err.message}`, 'danger');
    }
}

function renderTrendLineChart(labels, values, symbol) {
    const ctx = document.getElementById('trendLineChart').getContext('2d');
    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.map(l => `Day ${l}`),
            datasets: [{
                label: 'Daily Spending',
                data: values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.08)',
                borderWidth: 3,
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: '#0d6efd'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Spending: ${symbol}${ctx.parsed.y.toLocaleString('en-IN')}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: (val) => `${symbol}${val}` }
                }
            }
        }
    });
}

function renderCategoryDoughnutChart(breakdown, symbol) {
    const ctx = document.getElementById('categoryDoughnutChart').getContext('2d');
    if (categoryChart) categoryChart.destroy();

    const categories = Object.keys(breakdown);
    const amounts = Object.values(breakdown);

    const colors = [
        '#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0',
        '#6f42c1', '#d63384', '#fd7e14', '#20c997', '#6c757d', '#343a40'
    ];

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: colors.slice(0, categories.length),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${symbol}${ctx.parsed.toLocaleString('en-IN')}`
                    }
                }
            },
            cutout: '70%'
        }
    });
}

function renderMonthlyBarChart(comparisonData, symbol) {
    const ctx = document.getElementById('monthlyBarChart').getContext('2d');
    if (barChart) barChart.destroy();

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: comparisonData.map(d => d.month),
            datasets: [{
                label: 'Total Spending',
                data: comparisonData.map(d => d.total),
                backgroundColor: '#198754',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Total: ${symbol}${ctx.parsed.y.toLocaleString('en-IN')}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: (val) => `${symbol}${val}` }
                }
            }
        }
    });
}

function renderInsightsWidget(insights) {
    const container = document.getElementById('dashInsightsContainer');
    if (!insights || insights.length === 0) {
        container.innerHTML = `<div class="col-12 text-center text-muted py-2">No active alerts generated. Spending patterns are normal.</div>`;
        return;
    }

    container.innerHTML = insights.slice(0, 3).map(ins => {
        let badgeClass = 'bg-primary-subtle text-primary';
        if (ins.type === 'warning') badgeClass = 'bg-warning-subtle text-warning';
        if (ins.type === 'positive') badgeClass = 'bg-success-subtle text-success';

        return `
            <div class="col-12 col-md-4">
                <div class="p-3 bg-body-tertiary rounded-3 border h-100">
                    <div class="d-flex align-items-center justify-content-between mb-1">
                        <h6 class="fw-bold mb-0 text-truncate" style="max-width: 170px;">${ins.title}</h6>
                        <span class="badge ${badgeClass} text-capitalize">${ins.type}</span>
                    </div>
                    <p class="small text-muted mb-0">${ins.message}</p>
                </div>
            </div>`;
    }).join('');
}

function renderRecentTransactionsTable(transactions, symbol) {
    const tbody = document.getElementById('dashRecentTableBody');
    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No recent transactions recorded yet.</td></tr>`;
        return;
    }

    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td class="ps-3 text-nowrap">${t.date}</td>
            <td class="fw-semibold">${t.description} ${t.is_recurring ? '<span class="badge bg-info-subtle text-info ms-1">Recurring</span>' : ''}</td>
            <td><span class="badge bg-secondary-subtle text-secondary">${t.category}</span></td>
            <td>${t.payment_method}</td>
            <td class="text-end pe-3 fw-bold">₹${t.amount.toLocaleString('en-IN')}</td>
        </tr>
    `).join('');
}
