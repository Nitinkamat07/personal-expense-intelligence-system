from datetime import date
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Expense, Budget
from services.forecasting import forecaster
from services.insight_engine import insight_engine
from services.anomaly_detector import anomaly_detector

insight_bp = Blueprint('insights', __name__)

@insight_bp.route('/insights', methods=['GET'])
@login_required
def index():
    return render_template('insights.html')

@insight_bp.route('/api/insights', methods=['GET'])
@login_required
def get_insights():
    today = date.today()
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()

    result = insight_engine.generate_insights(
        user_expenses, user_budgets, current_user.monthly_budget or 25000.0, today
    )

    return jsonify({
        'success': True,
        'insights': result['insights'],
        'recommendations': result['recommendations'],
        'recurring_summary': {
            'monthly_total': result['recurring_monthly_total'],
            'count': result['recurring_count']
        }
    })

@insight_bp.route('/api/forecast', methods=['GET'])
@login_required
def get_forecast():
    today = date.today()
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    forecast = forecaster.generate_forecast(
        user_expenses, current_user.monthly_budget or 25000.0, today
    )
    return jsonify({'success': True, 'forecast': forecast})

@insight_bp.route('/api/anomalies', methods=['GET'])
@login_required
def get_anomalies():
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Run batch evaluation to make sure any pending anomaly detection is fresh
    anomaly_detector.batch_evaluate(user_expenses)
    db.session.commit()

    anomalies = [e.to_dict() for e in user_expenses if e.is_anomaly]
    return jsonify({
        'success': True,
        'count': len(anomalies),
        'anomalies': anomalies
    })

@insight_bp.route('/api/anomalies/<int:expense_id>/feedback', methods=['POST'])
@login_required
def anomaly_feedback(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    status = data.get('status') # valid, incorrect, ignored

    if status not in ['valid', 'incorrect', 'ignored']:
        return jsonify({'success': False, 'message': 'Invalid status choice.'}), 400

    expense.anomaly_status = status
    if status == 'incorrect':
        expense.is_anomaly = False

    db.session.commit()
    return jsonify({'success': True, 'expense': expense.to_dict()})
