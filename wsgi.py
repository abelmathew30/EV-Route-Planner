"""
wsgi.py — Production WSGI Entry Point for Render / Gunicorn
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
