import pytest
import io
from app import create_app
from config import TestingConfig
from models import db, User, Expense, Budget
from services.csv_service import CSVService

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = User(username='buser', email='buser@example.com')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    client = app.test_client()
    client.post('/login', json={'email': 'buser@example.com', 'password': 'pass123'})
    return client

def test_budget_setting_and_alerts(client, app):
    # Set Food budget
    res = client.post('/api/budgets', json={
        'category': 'Food',
        'amount': 5000.0,
        'month': 8,
        'year': 2026
    })
    assert res.status_code == 200

    # Add Food expense of 4200 (84% -> warning)
    client.post('/api/expenses', json={
        'description': 'Restaurant dinner',
        'amount': 4200.0,
        'category': 'Food',
        'date': '2026-08-05'
    })

    # Fetch Budgets
    b_res = client.get('/api/budgets?month=8&year=2026')
    assert b_res.status_code == 200
    data = b_res.get_json()
    
    food_b = next(b for b in data['category_budgets'] if b['category'] == 'Food')
    assert food_b['spent_amount'] == 4200.0
    assert food_b['percentage'] == 84.0
    assert food_b['status'] == 'warning'

def test_csv_import_and_export(client, app):
    csv_content = """Date,Description,Amount,Category,Payment Method
2026-08-01,Swiggy Lunch,350,Food,UPI
2026-08-02,Uber Ride,220,Transport,UPI
2026-08-01,Swiggy Lunch,350,Food,UPI
"""
    file_stream = io.BytesIO(csv_content.encode('utf-8'))
    
    with app.app_context():
        user = User.query.filter_by(username='buser').first()
        existing = Expense.query.filter_by(user_id=user.id).all()
        
        result = CSVService().process_csv_import(file_stream, user.id, existing)
        assert result['success'] is True
        assert result['imported'] == 2
        assert result['duplicates'] == 1
        assert result['skipped'] == 1

    # Test CSV Export
    exp_res = client.get('/api/export')
    assert exp_res.status_code == 200
    assert 'text/csv' in exp_res.content_type
    assert b'Swiggy Lunch' in exp_res.data
