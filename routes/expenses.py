from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from models import db, Expense
from services.categorizer import categorizer
from services.anomaly_detector import anomaly_detector
from config import Config

expense_bp = Blueprint('expenses', __name__)

@expense_bp.route('/expenses', methods=['GET'])
@login_required
def index():
    return render_template('expenses.html', categories=Config.CATEGORIES, payment_methods=Config.PAYMENT_METHODS)

@expense_bp.route('/api/expenses', methods=['GET'])
@login_required
def get_expenses():
    query = Expense.query.filter_by(user_id=current_user.id)

    # Search query
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Expense.description.ilike(f'%{search}%') | Expense.notes.ilike(f'%{search}%'))

    # Category filter
    category = request.args.get('category', '').strip()
    if category and category != 'All':
        query = query.filter_by(category=category)

    # Payment method filter
    payment_method = request.args.get('payment_method', '').strip()
    if payment_method and payment_method != 'All':
        query = query.filter_by(payment_method=payment_method)

    # Recurring filter
    recurring = request.args.get('recurring')
    if recurring == 'true':
        query = query.filter_by(is_recurring=True)

    # Date range filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        try:
            d_start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= d_start)
        except ValueError:
            pass
    if end_date:
        try:
            d_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= d_end)
        except ValueError:
            pass

    # Sort
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(Expense.date.desc(), Expense.id.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(Expense.date.asc(), Expense.id.asc())
    elif sort_by == 'amount_desc':
        query = query.order_by(Expense.amount.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Expense.amount.asc())

    expenses = query.all()
    return jsonify({
        'success': True,
        'count': len(expenses),
        'total_amount': float(round(sum(float(e.amount) for e in expenses), 2)),
        'expenses': [e.to_dict() for e in expenses]
    })

@expense_bp.route('/api/expenses', methods=['POST'])
@login_required
def create_expense():
    data = request.get_json() or {}
    
    amount = data.get('amount')
    description = str(data.get('description') or '').strip()
    category = str(data.get('category') or '').strip()
    date_str = data.get('date')
    payment_method = str(data.get('payment_method') or 'UPI').strip()
    notes = str(data.get('notes') or '').strip()
    is_recurring = bool(data.get('is_recurring', False))

    if amount is None or amount == '' or not description:
        return jsonify({'success': False, 'message': 'Amount and Description are required fields.'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid amount.'}), 400

    # Parse date
    if date_str:
        try:
            exp_date = datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
        except ValueError:
            exp_date = datetime.now().date()
    else:
        exp_date = datetime.now().date()

    # Intelligent ML Categorization if category not manually selected
    predicted_cat, confidence, is_confident = categorizer.predict(description)
    
    if not category or category == 'Auto-Detect' or 'Auto-Detect' in category:
        category = predicted_cat

    # Check Anomaly
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    is_anom, reason = anomaly_detector.evaluate_expense(user_expenses, amount, category, date_val=exp_date)

    expense = Expense(
        user_id=current_user.id,
        amount=amount,
        description=description,
        category=category,
        date=exp_date,
        payment_method=payment_method,
        notes=notes,
        is_recurring=is_recurring,
        predicted_category=predicted_cat,
        prediction_confidence=confidence,
        is_anomaly=is_anom,
        anomaly_reason=reason if is_anom else None
    )

    try:
        db.session.add(expense)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to save expense: {str(e)}'
        }), 500

    return jsonify({
        'success': True,
        'message': 'Expense recorded successfully!',
        'expense': expense.to_dict()
    }), 201

@expense_bp.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    if 'amount' in data:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'success': False, 'message': 'Amount must be greater than 0.'}), 400
            expense.amount = amount
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Invalid amount.'}), 400

    if 'description' in data:
        description = str(data['description'] or '').strip()
        if not description:
            return jsonify({'success': False, 'message': 'Description is required.'}), 400
        expense.description = description

    if 'category' in data:
        category = str(data['category'] or '').strip()
        if not category:
            return jsonify({'success': False, 'message': 'Category is required.'}), 400
        expense.category = category

    if 'payment_method' in data:
        expense.payment_method = str(data['payment_method'] or '').strip() or 'UPI'
    if 'notes' in data:
        expense.notes = str(data['notes'] or '').strip()
    if 'is_recurring' in data:
        expense.is_recurring = bool(data['is_recurring'])
    if 'date' in data and data['date']:
        try:
            expense.date = datetime.strptime(str(data['date']).strip(), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

    db.session.commit()
    return jsonify({'success': True, 'expense': expense.to_dict()})

@expense_bp.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Expense deleted.'})

@expense_bp.route('/api/expenses/categorize-preview', methods=['POST'])
@login_required
def categorize_preview():
    data = request.get_json() or {}
    description = data.get('description', '')
    predicted_cat, confidence, is_confident = categorizer.predict(description)
    
    return jsonify({
        'predicted_category': predicted_cat,
        'confidence': round(confidence, 2),
        'is_confident': is_confident
    })
