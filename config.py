import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env file if present
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    # Use environment variable, otherwise fallback to a default only for dev
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Fallback for dev only; production will override or fail
        SECRET_KEY = 'expense-intelligence-dev-fallback-key'
        
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Convert postgres:// to postgresql:// for SQLAlchemy 1.4+
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        # Add SSL mode for remote Postgres databases
        if "postgresql://" in db_url and "?" not in db_url:
            db_url += "?sslmode=require"
    
    # IMPORTANT: On Vercel, use DATABASE_URL with PostgreSQL (not SQLite in /tmp which is ephemeral)
    # To set up: Create a free Vercel Postgres DB and add DATABASE_URL to Vercel environment variables
    SQLALCHEMY_DATABASE_URI = db_url or (
        f"sqlite:///{os.path.join(BASE_DIR, 'expense_intelligence.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL connection pool settings for Vercel serverless
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "connect_args": {"connect_timeout": 10}
    } if db_url and "postgresql://" in str(db_url) else {}
    
    # ML & Upload Config
    ML_MODEL_DIR = os.path.join(BASE_DIR, 'ml', 'models')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Default Categories
    CATEGORIES = [
        "Food",
        "Transport",
        "Shopping",
        "Entertainment",
        "Bills",
        "Education",
        "Healthcare",
        "Travel",
        "Rent",
        "Utilities",
        "Other"
    ]
    
    PAYMENT_METHODS = [
        "Credit Card",
        "Debit Card",
        "UPI",
        "Net Banking",
        "Cash",
        "Other"
    ]

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # In production, require SECRET_KEY to be set in environment
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY environment variable is required in production!")
        return key

config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig,
    'default': DevelopmentConfig
}
