# ...existing code...
import os
import sys
from pathlib import Path

project_home = Path(__file__).resolve().parent
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

# Load a server-only .env when present (do NOT commit .env to git)
env_path = project_home / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=str(env_path))

# Import the Flask app object and expose as 'application'
# If your Flask object is named differently, change the import below.
from app import app as application

# ensure production defaults
application.config.setdefault('ENV', 'production')
application.config.setdefault('DEBUG', False)

# IMPORTANT: do not call socketio.run() or start servers here.
# PythonAnywhere runs the WSGI app for you.
# ...existing code...