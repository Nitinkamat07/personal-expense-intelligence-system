from datetime import datetime, date
import calendar
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Expense, Budget
from services.forecasting import forecaster
from services.insight_engine import insight_engine

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard_data():
    today = date.today()
    curr_year, curr_month = today.year, today.month

    if curr_month == 1:
        prev_month, prev_year = 12, curr_year - 1
    else:
        prev_month, prev_year = curr_month - 1, curr_year

    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()

    # Current & Last month expense lists
    curr_month_expenses = [e for e in user_expenses if e.date.year == curr_year and e.date.month == curr_month]
    prev_month_expenses = [e for e in user_expenses if e.date.year == prev_year and e.date.month == prev_month]

    total_curr_spending = sum(float(e.amount) for e in curr_month_expenses)
    total_prev_spending = sum(float(e.amount) for e in prev_month_expenses)

    # % change spending
    if total_prev_spending > 0:
        spending_change_pct = ((total_curr_spending - total_prev_spending) / total_prev_spending) * 100
    else:
        spending_change_pct = 0.0

    monthly_budget = float(current_user.monthly_budget or 25000.0)
    remaining_budget = max(monthly_budget - total_curr_spending, 0.0)
    days_elapsed = today.day
    avg_daily_spending = total_curr_spending / days_elapsed if days_elapsed > 0 else 0.0

    # Category breakdown for current month
    cat_breakdown = {}
    for e in curr_month_expenses:
        cat_breakdown[e.category] = cat_breakdown.get(e.category, 0.0) + float(e.amount)
    
    # Highest spending category
    if cat_breakdown:
        highest_category = max(cat_breakdown, key=cat_breakdown.get)
        highest_cat_amount = cat_breakdown[highest_category]
    else:
        highest_category = "N/A"
        highest_cat_amount = 0.0

    # Top expenses this month
    top_expenses = sorted(curr_month_expenses, key=lambda x: x.amount, reverse=True)[:5]

    # Recent transactions
    recent_transactions = sorted(user_expenses, key=lambda x: (x.date, x.id), reverse=True)[:7]

    # Spending Over Time (Daily spending trend for current month)
    days_in_month = calendar.monthrange(curr_year, curr_month)[1]
    daily_trend_labels = [f"{d}" for d in range(1, days_elapsed + 1)]
    daily_trend_values = [0.0] * days_elapsed

    for e in curr_month_expenses:
        d_idx = e.date.day - 1
        if d_idx < days_elapsed:
            daily_trend_values[d_idx] += float(e.amount)

    # Monthly comparison data (Last 6 months)
    monthly_comp = []
    for i in range(5, -1, -1):
        target_m = curr_month - i
        target_y = curr_year
        while target_m <= 0:
            target_m += 12
            target_y -= 1
        m_expenses = [e for e in user_expenses if e.date.year == target_y and e.date.month == target_m]
        m_label = datetime(target_y, target_m, 1).strftime('%b %Y')
        monthly_comp.append({
            'month': m_label,
            'total': round(sum(float(e.amount) for e in m_expenses), 2)
        })

    # Call forecasting & insight engine
    forecast_data = forecaster.generate_forecast(user_expenses, monthly_budget, today)
    insights_data = insight_engine.generate_insights(user_expenses, user_budgets, monthly_budget, today)
    unusual_expenses = [e.to_dict() for e in user_expenses if e.is_anomaly and e.anomaly_status == 'pending'][:3]

    return jsonify({
        'success': True,
        'summary': {
            'total_spending_this_month': round(total_curr_spending, 2),
            'total_spending_last_month': round(total_prev_spending, 2),
            'monthly_budget': round(monthly_budget, 2),
            'remaining_budget': round(remaining_budget, 2),
            'avg_daily_spending': round(avg_daily_spending, 2),
            'highest_spending_category': highest_category,
            'highest_category_amount': round(highest_cat_amount, 2),
            'transaction_count': len(curr_month_expenses),
            'spending_change_pct': round(spending_change_pct, 1),
            'currency_symbol': current_user.currency_symbol or '₹'
        },
        'category_breakdown': {k: round(v, 2) for k, v in cat_breakdown.items()},
        'daily_trend': {
            'labels': daily_trend_labels,
            'values': [round(v, 2) for v in daily_trend_values]
        },
        'monthly_comparison': monthly_comp,
        'top_expenses': [e.to_dict() for e in top_expenses],
        'recent_transactions': [e.to_dict() for e in recent_transactions],
        'forecast': forecast_data,
        'insights': insights_data['insights'],
        'recommendations': insights_data['recommendations'],
        'unusual_expenses': unusual_expenses
    })
