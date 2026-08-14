import pytest
from services.categorizer import ExpenseCategorizer
from services.anomaly_detector import AnomalyDetector
from services.forecasting import SpendingForecaster
from datetime import date
from models import Expense

def test_ml_categorizer_training_and_prediction():
    cat_engine = ExpenseCategorizer(model_dir='ml/test_models')
    
    descriptions = [
        "Swiggy dinner biryani",
        "Zomato food order",
        "KFC chicken meal",
        "McDonalds burger breakfast",
        "Uber ride to airport",
        "Ola cab fare",
        "Metro train ticket",
        "Auto rickshaw fare",
        "Amazon purchase headphones",
        "Flipkart sale shirt",
        "Myntra jacket buy",
        "Zara trousers shopping"
    ]
    categories = [
        "Food", "Food", "Food", "Food",
        "Transport", "Transport", "Transport", "Transport",
        "Shopping", "Shopping", "Shopping", "Shopping"
    ]

    cat_engine.train(descriptions, categories)

    pred, conf, is_conf = cat_engine.predict("Swiggy lunch")
    assert pred == "Food"
    assert conf > 0.0

    pred_t, conf_t, _ = cat_engine.predict("Uber cab to college")
    assert pred_t == "Transport"

def test_anomaly_detector_logic():
    detector = AnomalyDetector(min_history_records=3)
    
    # Create baseline food expenses
    history = [
        Expense(amount=200, category='Food'),
        Expense(amount=350, category='Food'),
        Expense(amount=400, category='Food'),
        Expense(amount=250, category='Food'),
        Expense(amount=300, category='Food')
    ]

    # Test normal amount
    is_anom, reason = detector.evaluate_expense(history, 380, 'Food')
    assert is_anom is False

    # Test anomalous spike
    is_anom_spike, reason_spike = detector.evaluate_expense(history, 4800, 'Food')
    assert is_anom_spike is True
    assert 'higher than your median Food expense' in reason_spike

def test_spending_forecaster():
    fc = SpendingForecaster()
    
    # 1. Test insufficient history warning (less than 3 distinct months)
    expenses = [
        Expense(amount=500, date=date(2026, 8, 1)),
        Expense(amount=1500, date=date(2026, 8, 5)),
        Expense(amount=2000, date=date(2026, 8, 10))
    ]

    forecast = fc.generate_forecast(expenses, 25000.0, target_date=date(2026, 8, 12))
    assert forecast['current_spending'] == 4000.0
    assert forecast['days_elapsed'] == 12
    assert forecast['predicted_total_spending'] > 4000.0
    assert forecast['next_month_forecast']['evaluation']['status'] == 'insufficient_data'

    # 2. Test sufficient history evaluation (3+ months)
    many_expenses = [
        # Month 1
        Expense(amount=1000, date=date(2026, 5, 15), category='Food'),
        Expense(amount=2000, date=date(2026, 5, 20), category='Shopping'),
        # Month 2
        Expense(amount=1200, date=date(2026, 6, 15), category='Food'),
        Expense(amount=2200, date=date(2026, 6, 20), category='Shopping'),
        # Month 3
        Expense(amount=1100, date=date(2026, 7, 15), category='Food'),
        Expense(amount=2100, date=date(2026, 7, 20), category='Shopping'),
        # Month 4 (current month)
        Expense(amount=1300, date=date(2026, 8, 15), category='Food')
    ]
    
    forecast_eval = fc.generate_forecast(many_expenses, 10000.0, target_date=date(2026, 8, 16))
    eval_metrics = forecast_eval['next_month_forecast']['evaluation']
    assert eval_metrics['status'] == 'success'
    assert 'metrics' in eval_metrics
    assert 'model_mae' in eval_metrics['metrics']
    assert 'baseline_mae' in eval_metrics['metrics']

def test_ml_metrics_retrieval():
    from services.categorizer import categorizer
    metrics = categorizer.get_metrics()
    # It should load the metrics from the ml/train_categorizer.py run
    if metrics:
        assert 'accuracy' in metrics
        assert 'f1_macro' in metrics
