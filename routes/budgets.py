from datetime import date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Budget, Expense
from config import Config

budget_bp = Blueprint('budgets', __name__)

@budget_bp.route('/budgets', methods=['GET'])
@login_required
def index():
    return render_template('budgets.html', categories=Config.CATEGORIES)

@budget_bp.route('/api/budgets', methods=['GET'])
@login_required
def get_budgets():
    today = date.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    m_expenses = [e for e in expenses if e.date.year == year and e.date.month == month]

    cat_spending = {}
    for e in m_expenses:
        cat_spending[e.category] = cat_spending.get(e.category, 0.0) + float(e.amount)

    budget_list = []
    total_allocated = 0.0

    for b in budgets:
        spent = cat_spending.get(b.category, 0.0)
        b_amount_f = float(b.amount)
        pct = (spent / b_amount_f * 100) if b_amount_f > 0 else 0.0
        
        if pct >= 100:
            status = 'exceeded'
            warning_msg = f"You have exceeded your {b.category} budget by {pct - 100:.0f}%!"
        elif pct >= 80:
            status = 'warning'
            warning_msg = f"You have used {pct:.0f}% of your {b.category} budget."
        else:
            status = 'normal'
            warning_msg = None

        total_allocated += b_amount_f
        budget_list.append({
            'id': b.id,
            'category': b.category,
            'budget_amount': round(b_amount_f, 2),
            'spent_amount': round(spent, 2),
            'remaining_amount': round(max(b_amount_f - spent, 0.0), 2),
            'percentage': round(pct, 1),
            'status': status,
            'warning_msg': warning_msg
        })

    # Overall Monthly Budget tracking
    total_m_spent = sum(float(e.amount) for e in m_expenses)
    overall_budget = float(current_user.monthly_budget or 25000.0)
    overall_pct = (total_m_spent / overall_budget * 100) if overall_budget > 0 else 0.0

    return jsonify({
        'success': True,
        'month': month,
        'year': year,
        'overall_budget': round(overall_budget, 2),
        'overall_spent': round(total_m_spent, 2),
        'overall_percentage': round(overall_pct, 1),
        'total_allocated': round(total_allocated, 2),
        'category_budgets': budget_list
    })

@budget_bp.route('/api/budgets', methods=['POST'])
@login_required
def set_budget():
    data = request.get_json() or {}
    category = data.get('category', '').strip()
    amount = data.get('amount')
    today = date.today()
    month = data.get('month', today.month)
    year = data.get('year', today.year)

    if not category or amount is None:
        return jsonify({'success': False, 'message': 'Category and Amount are required.'}), 400

    try:
        amount = float(amount)
        if amount < 0:
            return jsonify({'success': False, 'message': 'Amount cannot be negative.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format.'}), 400

    budget = Budget.query.filter_by(
        user_id=current_user.id, category=category, month=month, year=year
    ).first()

    if budget:
        budget.amount = amount
    else:
        budget = Budget(
            user_id=current_user.id, category=category, amount=amount, month=month, year=year
        )
        db.session.add(budget)

    db.session.commit()
    return jsonify({'success': True, 'budget': budget.to_dict()})

@budget_bp.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Category budget deleted.'})
