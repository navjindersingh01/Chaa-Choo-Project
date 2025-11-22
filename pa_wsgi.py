"""
PythonAnywhere-friendly WSGI entrypoint.

Point PythonAnywhere's "WSGI configuration file" to this file (or import it from there).
This file exposes the WSGI application object named `application`.

Notes:
- This loads a local `.env` file if present (do not commit secrets).
- If you need Socket.IO support, additional configuration is required on the server.
"""
import os
import sys
from dotenv import load_dotenv

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env if present (safe to ignore if not)
load_dotenv(os.path.join(project_home, '.env'))

# Import the Flask app object. The project defines `app` in `app.py`.
try:
    from app import app as application  # `application` is what PA expects
except Exception:
    # Fall back to importing app then assigning
    from app import app
    application = app

# Ensure production config when deployed on PA
try:
    application.config['ENV'] = 'production'
    application.config['DEBUG'] = False
except Exception:
    pass

# Security defaults for production on PythonAnywhere
try:
    # Ensure session cookies are secure when served over HTTPS
    application.config.setdefault('SESSION_COOKIE_SECURE', True)
    # Prevent cross-site request forgery via lax same-site policy
    application.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    # Prefer server-side session lifetime control
    application.config.setdefault('PERMANENT_SESSION_LIFETIME', 60 * 60 * 24)  # seconds (1 day)
except Exception:
    pass
