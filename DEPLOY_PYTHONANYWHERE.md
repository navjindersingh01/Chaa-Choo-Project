**Deploying Chaa Choo on PythonAnywhere**

1) Prepare the server
- Create a virtualenv on PythonAnywhere and install dependencies:
```bash
python3 -m venv ~/venvs/chaachoo
source ~/venvs/chaachoo/bin/activate
pip install -r /home/<your-username>/path/to/project/requirements.txt
```

2) Copy environment variables
- Copy `.env.example` to `.env` locally or on the server and fill in production values.
- On PythonAnywhere you can instead set environment variables in the Web tab.

3) Create the database and seed test data
- If you use PythonAnywhere's MySQL:
  - Create a MySQL database via the Databases tab and note the DB name, user and host.
  - Set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` in the Web tab or `.env`.
- To create tables and seed test data, run the included setup script (on PythonAnywhere inside the virtualenv):
```bash
cd /home/<your-username>/path/to/project
source ~/venvs/chaachoo/bin/activate
python3 scripts/setup_db.py
```
This script will create `users`, `items`, `orders`, `order_items`, and `inventory` tables and add sample users.

4) WSGI configuration
- In the Web tab set the "Source code" and "Working directory" to your project path.
- Point the WSGI file to the standard PythonAnywhere WSGI file and import `application` from `pa_wsgi.py`:
```python
import sys
path = '/home/<your-username>/path/to/project'
if path not in sys.path:
    sys.path.insert(0, path)
from pa_wsgi import application
```

5) Static files
- Map URL `/static` to `/home/<your-username>/path/to/project/static`.

6) Socket.IO notes
- PythonAnywhere has limitations for WebSockets. The app uses Flask-SocketIO; long-polling may work but real-time WebSockets require a provider that supports them (or a paid plan). The app will still work without WebSockets; dashboards will refresh via AJAX endpoints.

7) Security checklist
- Do NOT commit `.env` to GitHub. Keep secrets in PA Web tab or server-only `.env`.
- Ensure `SECRET_KEY` is set to a strong random value.
- Verify `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_SAMESITE` are set (this repo sets defaults in `pa_wsgi.py`).

8) Start and test
- Reload the web app in the Web tab and check the error log for issues.
- Visit `/health` to confirm DB connectivity.

If you want, I can:
- Generate a one-line script to set up the virtualenv and run `scripts/setup_db.py` on PA.
- Run `pip freeze` locally to refresh `requirements.txt`.
