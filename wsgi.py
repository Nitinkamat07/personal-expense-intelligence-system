"""
WSGI entry point for Vercel deployment
"""
from app import app, db
import os

# Ensure database directory exists
os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)

if __name__ == "__main__":
    app.run()
