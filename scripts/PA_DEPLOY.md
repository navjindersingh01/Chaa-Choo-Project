**PythonAnywhere Deployment**

- **Create a virtualenv** on PythonAnywhere (choose same Python version used locally):
```
python3 -m venv ~/venvs/chaachoo
source ~/venvs/chaachoo/bin/activate
pip install -r /home/<your-username>/path/to/project/requirements.txt
```

- **Upload project**: push to GitHub and clone on PythonAnywhere, or upload via SFTP.

- **Environment variables**: Do NOT commit secrets. On PythonAnywhere Web tab, set these env vars:
  - `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SECRET_KEY` (use production values)
  - Alternatively, create a `.env` file in project root (should be listed in `.gitignore`) and copy values there.

- **WSGI configuration**: In the Web tab set:
  - Source code: `/home/<your-username>/path/to/project`
  - Working directory: same as source
  - WSGI file: point to the built-in file and import `pa_wsgi` or set the path to `pa_wsgi.py` created in this repo.
    Example WSGI file content (PythonAnywhere default file):
```python
import sys
path = '/home/<your-username>/path/to/project'
if path not in sys.path:
    sys.path.insert(0, path)
from pa_wsgi import application
```

- **Static files**: map `/static` -> `/home/<your-username>/path/to/project/static` in the Web tab's Static files section.

- **Database**: If using PythonAnywhere's MySQL, use the DB credentials provided by PA and set `DB_HOST`, `DB_USER`, `DB_NAME` accordingly. If using external DB, ensure your DB allows connections from PythonAnywhere and use its host.

- **Socket.IO**: PythonAnywhere does not support long-running websocket servers on standard accounts. If your app relies on Socket.IO, you may need an alternative hosting provider or use polling fallback. See Flask-SocketIO docs.

- **Reload app**: After configuration, press Reload in the Web tab and check the error log for issues.
