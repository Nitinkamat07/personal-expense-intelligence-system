import pytest
from datetime import date
from app import create_app
from config import TestingConfig
from models import db, User, Expense, Budget
from services.copilot_service import copilot_service

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed test user
        user = User(username='copilotuser', email='copilot@example.com')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    client = app.test_client()
    client.post('/login', json={'email': 'copilot@example.com', 'password': 'pass123'})
    return client

def test_copilot_service_top_spending(app):
    with app.app_context():
        user = User.query.filter_by(username='copilotuser').first()
        
        # Seed expenses for current month
        today = date.today()
        exp1 = Expense(user_id=user.id, amount=1200.0, category='Transport', date=today, description='Uber ride')
        exp2 = Expense(user_id=user.id, amount=3000.0, category='Food', date=today, description='Swiggy dinner')
        db.session.add_all([exp1, exp2])
        db.session.commit()

        # Query top category
        result = copilot_service.process_query(user, "where did I spend the most money?")
        assert result['success'] is True
        assert result['data']['top_category'] == 'Food'
        assert result['data']['top_amount'] == 3000.0
        assert 'Food' in result['answer']

def test_copilot_service_subscriptions(app):
    with app.app_context():
        user = User.query.filter_by(username='copilotuser').first()
        
        # Seed recurring expenses
        today = date.today()
        sub = Expense(user_id=user.id, amount=649.0, category='Entertainment', date=today, description='Netflix subscription', is_recurring=True)
        db.session.add(sub)
        db.session.commit()

        result = copilot_service.process_query(user, "show me my subscriptions")
        assert result['success'] is True
        assert result['data']['count'] == 1
        assert result['data']['total'] == 649.0
        assert 'Netflix' in result['answer']

def test_copilot_service_budget(app):
    with app.app_context():
        user = User.query.filter_by(username='copilotuser').first()
        today = date.today()

        # Seed category budget & expense exceeding it
        b = Budget(user_id=user.id, category='Food', amount=500.0, month=today.month, year=today.year)
        exp = Expense(user_id=user.id, amount=600.0, category='Food', date=today, description='Spicy Dinner')
        db.session.add_all([b, exp])
        db.session.commit()

        result = copilot_service.process_query(user, "How much of my budget is left?")
        assert result['success'] is True
        assert result['data']['total_spent'] == 600.0
        assert 'Food' in result['answer']
        assert 'Over by' in result['answer']

def test_copilot_route_ask(client):
    # Valid query
    res = client.post('/api/copilot', json={'query': 'What is my budget?'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'budget' in data['query'].lower()

    # Empty query
    res_empty = client.post('/api/copilot', json={'query': ''})
    assert res_empty.status_code == 400
