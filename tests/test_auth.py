import pytest
from app import create_app
from config import TestingConfig
from models import db, User

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_user_registration(client, app):
    response = client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'monthly_budget': 20000
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.check_password('password123') is True

def test_user_login_and_session(client, app):
    with app.app_context():
        u = User(username='loginuser', email='login@example.com')
        u.set_password('mysecret')
        db.session.add(u)
        db.session.commit()

    # Login with valid credentials
    resp = client.post('/login', json={
        'email': 'login@example.com',
        'password': 'mysecret'
    })
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    # Test protected route access
    dash_resp = client.get('/api/dashboard')
    assert dash_resp.status_code == 200
    assert dash_resp.get_json()['success'] is True

    # Logout
    logout_resp = client.get('/logout', follow_redirects=True)
    assert logout_resp.status_code == 200

def test_duplicate_username_registration(client, app):
    # Create initial user
    with app.app_context():
        u = User(username='dupuser', email='dup1@example.com')
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()

    # Attempt to register duplicate username
    response = client.post('/register', json={
        'username': 'dupuser',
        'email': 'dup2@example.com',
        'password': 'password123',
        'monthly_budget': 20000
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Username already registered' in data['message']

def test_duplicate_email_registration(client, app):
    # Create initial user
    with app.app_context():
        u = User(username='dupuser1', email='dup@example.com')
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()

    # Attempt to register duplicate email
    response = client.post('/register', json={
        'username': 'dupuser2',
        'email': 'dup@example.com',
        'password': 'password123',
        'monthly_budget': 20000
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Email address already registered' in data['message']

def test_invalid_password_login(client, app):
    with app.app_context():
        u = User(username='pwuser', email='pw@example.com')
        u.set_password('realpassword')
        db.session.add(u)
        db.session.commit()

    # Login with invalid password
    resp = client.post('/login', json={
        'email': 'pw@example.com',
        'password': 'wrongpassword'
    })
    assert resp.status_code == 401
    assert resp.get_json()['success'] is False

