import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config_by_name
from models import db, User

csrf = CSRFProtect()

def create_app(config_class=None):
    if config_class is None:
        env = os.environ.get('FLASK_ENV') or 'dev'
        config_class = config_by_name.get(env, config_by_name['default'])
        
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Init database
    db.init_app(app)

    # Init Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.expenses import expense_bp
    from routes.dashboard import dashboard_bp
    from routes.budgets import budget_bp
    from routes.insights import insight_bp
    from routes.csv_io import csv_bp
    from routes.copilot import copilot_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(insight_bp)
    app.register_blueprint(csv_bp)
    app.register_blueprint(copilot_bp)

    @app.route('/landing')
    def landing():
        return render_template('landing.html')

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', content="<div class='container py-5 text-center'><h2>404 - Page Not Found</h2><a href='/dashboard' class='btn btn-primary mt-3'>Back to Dashboard</a></div>"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('base.html', content="<div class='container py-5 text-center'><h2>500 - Internal Server Error</h2><a href='/dashboard' class='btn btn-primary mt-3'>Back to Dashboard</a></div>"), 500

    # Ensure the schema exists without reseeding or recreating production data.
    with app.app_context():
        try:
            db.create_all()
            
            # Auto-seed demo user if database is empty (for first-time deployments)
            try:
                if User.query.count() == 0:
                    demo_user = User(
                        username='demo',
                        email='demo@expense.ai',
                        monthly_budget=25000.0,
                        currency_symbol='₹'
                    )
                    demo_user.set_password('password123')
                    db.session.add(demo_user)
                    db.session.commit()
                    print("✓ Demo user created: demo@expense.ai / password123")
            except Exception as e:
                print(f"Note: Could not check/create demo user: {e}")
                db.session.rollback()
            
            # Train ML categorizer on sample data (if not already trained)
            try:
                from services.categorizer import categorizer
                import pandas as pd
                
                # Check if model needs training
                if not hasattr(categorizer.pipeline, 'classes_') or len(categorizer.pipeline.classes_) == 0:
                    sample_data_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_transactions.csv')
                    if os.path.exists(sample_data_path):
                        df = pd.read_csv(sample_data_path)
                        if len(df) > 0 and 'Description' in df.columns and 'Category' in df.columns:
                            categorizer.train(df['Description'].tolist(), df['Category'].tolist())
                            print("✓ ML Categorizer trained on sample data")
            except Exception as e:
                print(f"Warning: Could not train categorizer: {e}")
        except Exception as e:
            print(f"Warning: Database initialization error: {e}")
            print("App will attempt to initialize database on first request.")

    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app

app = create_app()

if __name__ == '__main__':
    print("Starting Personal Expense Intelligence Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
