import pytest
from datetime import date
from app import create_app
from config import TestingConfig
from models import db, User, Expense

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed test user
        user = User(username='expuser', email='exp@example.com')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    client = app.test_client()
    client.post('/login', json={'email': 'exp@example.com', 'password': 'pass123'})
    return client

def test_expense_crud(client, app):
    # 1. Create Expense
    res = client.post('/api/expenses', json={
        'description': 'Swiggy dinner order',
        'amount': 450.0,
        'category': 'Food',
        'payment_method': 'UPI',
        'date': '2026-08-10'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    exp_id = data['expense']['id']

    # 2. Get Expenses list
    res_list = client.get('/api/expenses')
    assert res_list.status_code == 200
    list_data = res_list.get_json()
    assert list_data['count'] == 1
    assert list_data['total_amount'] == 450.0

    # 3. Update Expense
    res_upd = client.put(f'/api/expenses/{exp_id}', json={
        'amount': 500.0,
        'description': 'Swiggy dinner family feast'
    })
    assert res_upd.status_code == 200
    assert res_upd.get_json()['expense']['amount'] == 500.0

    # 4. Delete Expense
    res_del = client.delete(f'/api/expenses/{exp_id}')
    assert res_del.status_code == 200
    assert res_del.get_json()['success'] is True

    # Verify empty list
    res_list_empty = client.get('/api/expenses')
    assert res_list_empty.get_json()['count'] == 0

def test_expense_strict_user_isolation(client, app):
    # Create User B and User B's expense
    with app.app_context():
        user_b = User(username='userb', email='userb@example.com')
        user_b.set_password('pass123')
        db.session.add(user_b)
        db.session.commit()

        exp_b = Expense(
            user_id=user_b.id,
            amount=1500.0,
            description="User B private expense",
            category="Shopping",
            date=date(2026, 8, 11)
        )
        db.session.add(exp_b)
        db.session.commit()
        exp_b_id = exp_b.id

    # User A (logged in client) tries to read/edit/delete User B's expense
    # 1. Update attempt
    res_upd = client.put(f'/api/expenses/{exp_b_id}', json={'amount': 2000.0})
    assert res_upd.status_code == 404

    # 2. Delete attempt
    res_del = client.delete(f'/api/expenses/{exp_b_id}')
    assert res_del.status_code == 404

    # 3. Check that it doesn't show up in User A's GET expenses list
    res_list = client.get('/api/expenses')
    assert res_list.status_code == 200
    assert not any(e['id'] == exp_b_id for e in res_list.get_json()['expenses'])

def test_invalid_expense_inputs(client, app):
    # 1. Zero/Negative amount
    res = client.post('/api/expenses', json={
        'description': 'Free meal',
        'amount': 0.0,
        'category': 'Food'
    })
    assert res.status_code == 400
    assert res.get_json()['success'] is False

    # 2. Negative amount
    res = client.post('/api/expenses', json={
        'description': 'Refunding',
        'amount': -100.0,
        'category': 'Food'
    })
    assert res.status_code == 400

    # 3. Empty description
    res = client.post('/api/expenses', json={
        'description': '',
        'amount': 100.0,
        'category': 'Food'
    })
    assert res.status_code == 400

    # 4. Invalid date format
    res = client.post('/api/expenses', json={
        'description': 'Dinner',
        'amount': 100.0,
        'category': 'Food',
        'date': '12-08-2026' # incorrect format
    })
    # The route falls back to today's date rather than crashing
    assert res.status_code == 201

def test_dashboard_api(client, app):
    # 1. Add some initial expenses
    client.post('/api/expenses', json={
        'description': 'Office Lunch',
        'amount': 350.0,
        'category': 'Food',
        'date': date.today().strftime('%Y-%m-%d')
    })
    client.post('/api/expenses', json={
        'description': 'Bus ticket',
        'amount': 50.0,
        'category': 'Transport',
        'date': date.today().strftime('%Y-%m-%d')
    })

    # 2. Query Dashboard
    res = client.get('/api/dashboard')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['summary']['total_spending_this_month'] == 400.0
    assert data['summary']['transaction_count'] == 2
    assert data['category_breakdown']['Food'] == 350.0
    assert data['category_breakdown']['Transport'] == 50.0


