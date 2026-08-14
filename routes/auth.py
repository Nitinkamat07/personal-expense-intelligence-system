from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            monthly_budget = float(data.get('monthly_budget', 25000.0))
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            monthly_budget = float(request.form.get('monthly_budget', 25000.0))

        if not username or not email or not password:
            msg = 'All fields are required.'
            return jsonify({'success': False, 'message': msg}), 400 if request.is_json else (flash(msg, 'danger'), render_template('register.html'))[1]

        if User.query.filter_by(username=username).first():
            msg = 'Username already registered.'
            return jsonify({'success': False, 'message': msg}), 400 if request.is_json else (flash(msg, 'danger'), render_template('register.html'))[1]

        if User.query.filter_by(email=email).first():
            msg = 'Email address already registered.'
            return jsonify({'success': False, 'message': msg}), 400 if request.is_json else (flash(msg, 'danger'), render_template('register.html'))[1]

        user = User(username=username, email=email, monthly_budget=monthly_budget)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('dashboard.index')})
        flash('Account created successfully! Welcome to Personal Expense Intelligence.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email_raw = data.get('email', '')
            password = data.get('password', '')
        else:
            email_raw = request.form.get('email', '')
            password = request.form.get('password', '')

        email_clean = str(email_raw).strip().lower()

        user = User.query.filter(
            (db.func.lower(User.email) == email_clean) | 
            (db.func.lower(User.username) == email_clean)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard.index')})
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            msg = 'Invalid email/username or password.'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 401
            flash(msg, 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        data = request.get_json() or {}
        if 'monthly_budget' in data:
            current_user.monthly_budget = float(data['monthly_budget'])
        if 'currency_symbol' in data:
            current_user.currency_symbol = data['currency_symbol']
        db.session.commit()
        return jsonify({'success': True, 'user': current_user.to_dict()})

    return jsonify(current_user.to_dict())
