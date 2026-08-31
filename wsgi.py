"""
WSGI entry point for Vercel deployment
"""
from app import app

# Export the Flask app for Vercel
if __name__ == "__main__":
    app.run()

