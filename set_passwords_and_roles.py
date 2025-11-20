"""
One-off script to ensure bob, charlie, diana, eve have password '11111111'
and to update any 'stakeholder' role to 'manager'.
Run with venv Python: ./venv/bin/python set_passwords_and_roles.py
"""
from werkzeug.security import generate_password_hash
import mysql.connector
import os
import traceback

# load config if available
try:
    import config
    DB_HOST = config.DB_HOST
    DB_USER = config.DB_USER
    DB_PASSWORD = config.DB_PASSWORD
    DB_NAME = config.DB_NAME
except Exception:
    DB_HOST = os.getenv('DB_HOST','127.0.0.1')
    DB_USER = os.getenv('DB_USER','root')
    DB_PASSWORD = os.getenv('DB_PASSWORD','')
    DB_NAME = os.getenv('DB_NAME','cafe_ca3')

users_to_update = ['bob','charlie','diana','eve']
new_password = '11111111'

pw_hash = generate_password_hash(new_password)

try:
    cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, auth_plugin='mysql_native_password')
    cur = cnx.cursor()

    for u in users_to_update:
        cur.execute("SELECT id, username, role FROM users WHERE username=%s", (u,))
        row = cur.fetchone()
        if not row:
            print(f"User {u} not found, skipping")
            continue
        uid, uname, role = row
        updates = []
        params = []
        # update password
        updates.append('password_hash=%s')
        params.append(pw_hash)
        # if role is stakeholder, map to manager
        if role == 'stakeholder':
            updates.append('role=%s')
            params.append('manager')
        params.append(uname)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE username=%s"
        cur.execute(sql, tuple(params))
        print(f"Updated user {uname}")

    cnx.commit()
    cur.close()
    cnx.close()
    print('Done updating users')
except Exception:
    print('Error:')
    print(traceback.format_exc())
