# tools/check_and_seed_items.py
import os
import sys
import json
import mysql.connector

# Read env vars with sensible fallbacks. Allow a DATABASE_URL like mysql://user:pass@host/db
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS') or os.getenv('DB_PASSWORD') or os.getenv('MYSQL_PWD') or ''
DB_NAME = os.getenv('DB_NAME') or os.getenv('DATABASE_NAME')
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and not DB_NAME:
    try:
        from urllib.parse import urlparse
        p = urlparse(DATABASE_URL)
        if p.scheme and 'mysql' in p.scheme:
            DB_USER = DB_USER or (p.username if p.username else DB_USER)
            DB_PASS = DB_PASS or (p.password if p.password else DB_PASS)
            DB_HOST = DB_HOST or (p.hostname if p.hostname else DB_HOST) or '127.0.0.1'
            if p.path:
                DB_NAME = p.path.lstrip('/')
    except Exception:
        print('WARN: failed to parse DATABASE_URL; continuing with raw env values')

DB_HOST = DB_HOST or '127.0.0.1'
DB_USER = DB_USER or 'root'
if not DB_NAME:
    print("ERROR: DB_NAME (or DATABASE_NAME or parsed DATABASE_URL) not set in env. Export DB_NAME and retry.")
    sys.exit(1)

print('Connecting to:', DB_HOST, DB_USER, DB_NAME)
try:
    cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, auth_plugin='mysql_native_password')
except mysql.connector.Error as e:
    print('Connection failed:', e)
    sys.exit(1)

cur = cnx.cursor(dictionary=True)

# Create items table if it doesn't exist
create_sql = """
CREATE TABLE IF NOT EXISTS items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  category VARCHAR(128) DEFAULT NULL,
  description TEXT,
  image VARCHAR(255),
  tags TEXT,
  veg TINYINT(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""
try:
    cur.execute(create_sql)
    cnx.commit()
    print('Ensured `items` table exists.')
except Exception as e:
    print('Failed creating items table:', e)

# Check existing items
try:
    cur.execute('SELECT COUNT(*) AS cnt FROM items')
    cnt = cur.fetchone().get('cnt', 0)
    print('Existing items count:', cnt)
except Exception as e:
    print('Failed to count items:', e)
    cnt = 0

if cnt == 0:
    print('Seeding sample items...')
    seed = [
        ('Assam Tea', 49.00, 'Beverages'),
        ('Masala Chai', 59.00, 'Beverages'),
        ('Veg Sandwich', 99.00, 'Snacks')
    ]
    for name, price, cat in seed:
        try:
            cur.execute('INSERT INTO items (name, price, category) VALUES (%s,%s,%s)', (name, price, cat))
        except Exception as e:
            print('Insert failed for', name, e)
    cnx.commit()
    print('Inserted sample items.')

# Show items
try:
    cur.execute('SELECT id, name, price FROM items ORDER BY id LIMIT 50')
    rows = cur.fetchall()
    print('items:')
    print(json.dumps(rows, indent=2, default=str))
except Exception as e:
    print('Failed to select items:', e)

cur.close()
cnx.close()
