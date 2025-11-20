"""
WSGI entry point for production deployment
This file is used by Gunicorn to launch the Flask application
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.production
load_dotenv('.env.production')

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, socketio

# Ensure production settings
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

if __name__ == '__main__':
    # This is only for local testing, production uses Gunicorn
    socketio.run(app, host='0.0.0.0', port=5000)
