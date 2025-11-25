# Consolidated imports and app/config initialization
import traceback
import logging
import os
import json
import csv
from io import StringIO
from datetime import datetime, timedelta

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Basic runtime flags
DEBUG = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes')
FLASK_ENV = os.getenv('FLASK_ENV', 'production').lower()
is_dev = FLASK_ENV in ('development', 'dev') or DEBUG

# Configure logging
log_file = os.getenv("LOG_FILE", "error.log")
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    filename=log_file,
    level=log_level,
    format='%(asctime)s %(levelname)s: %(message)s'
)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from functools import wraps

# Read DB config from environment. Support multiple common env var names and
# a single DATABASE_URL value for convenience (mysql://user:pass@host/dbname).
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
# Accept either DB_PASSWORD or DB_PASS
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME") or os.getenv('DATABASE_NAME')

# If a DATABASE_URL is provided, parse it (format: mysql://user:pass@host/db)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    try:
        from urllib.parse import urlparse
        p = urlparse(DATABASE_URL)
        # p.scheme, p.username, p.password, p.hostname, p.path
        if p.scheme and 'mysql' in p.scheme:
            DB_USER = DB_USER or (p.username if p.username else DB_USER)
            DB_PASSWORD = DB_PASSWORD or (p.password if p.password else DB_PASSWORD)
            DB_HOST = DB_HOST or (p.hostname if p.hostname else DB_HOST)
            # path starts with /dbname
            if p.path:
                DB_NAME = DB_NAME or p.path.lstrip('/')
    except Exception:
        logging.debug('Failed to parse DATABASE_URL: ' + traceback.format_exc())

# Fallback defaults if still not set
DB_HOST = DB_HOST or '127.0.0.1'
DB_USER = DB_USER or 'root'
DB_PASSWORD = DB_PASSWORD or os.getenv('MYSQL_PWD') or '11111111'
DB_NAME = DB_NAME or 'cafe_ca3'

# Create single Flask app instance
app = Flask(__name__)

# Load environment-driven settings
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-for-local'),
    'DEBUG': DEBUG,
    'ENV': FLASK_ENV,
    'PROPAGATE_EXCEPTIONS': True,
    'JSON_SORT_KEYS': False,
    'SESSION_COOKIE_SECURE': False if is_dev else os.getenv('SESSION_COOKIE_SECURE', 'true').lower() in ('1','true','yes'),
    'SESSION_COOKIE_SAMESITE': os.getenv('SESSION_COOKIE_SAMESITE', 'Lax'),
    'PERMANENT_SESSION_LIFETIME': timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', str(60*60*24*7)))
    )
})

# Attempt to apply config classes from config.py if present
try:
    from config import DevelopmentConfig, ProductionConfig
    cfg = DevelopmentConfig if FLASK_ENV in ('development', 'dev') else ProductionConfig
    app.config.from_object(cfg)
except Exception:
    # keep env-driven config if config module isn't available
    logging.debug('config.py not loaded; using environment-driven config')

# Ensure secret is set on app
app.secret_key = app.config.get('SECRET_KEY', app.secret_key)

# Upload settings for menu images
app.config['MENU_IMAGE_FOLDER'] = os.path.join(app.root_path, 'static', 'images', 'menu')
os.makedirs(app.config['MENU_IMAGE_FOLDER'], exist_ok=True)
ALLOWED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.svg', '.gif'}

# Configure SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=DEBUG,
    engineio_logger=DEBUG,
    async_mode='threading'
)

# ----- DB HELPER -----
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, auth_plugin='mysql_native_password'
        )
    except Exception:
        logging.error("DB connection failed:\n" + traceback.format_exc())
        raise


# ----- AUTH & ROLE DECORATORS -----
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'role' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash("Unauthorized for this role.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ----- ROUTES -----
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Check database connection
        db = get_db_connection()
        cur = db.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        db.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'environment': FLASK_ENV
        }), 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/')
def index():
    # public home page - menu preview
    # Prefer the authored JSON menu for quick edits; fallback to DB when absent
    json_path = os.path.join(app.root_path, 'data', 'menu.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                menu = json.load(f)
            # Flatten first N items for preview (preserve id/name/category/price)
            items = []
            for cat in menu.get('categories', []):
                for it in cat.get('items', []):
                    items.append({'id': it.get('id'), 'name': it.get('name'), 'category': cat.get('label'), 'price': it.get('price'), 'image': it.get('image'), 'description': it.get('description')})
                    if len(items) >= 12:
                        break
                if len(items) >= 12:
                    break
            return render_template('index.html', items=items)
        except Exception as e:
            logging.error(f"Failed to load menu.json: {e}")

    # Fallback: read from DB
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, category, price FROM items LIMIT 12;")
    items = cur.fetchall()
    cur.close()
    db.close()
    return render_template('index.html', items=items)

@app.route('/order')
def order_page():
    """Public order page for customers to place orders without login."""
    return render_template('order.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # simple login form (username + password)
    if request.method == 'POST':
        # Trim whitespace and normalize username to lowercase to avoid accidental mismatches
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        logging.info(f"Login attempt for username: {username}")
        
        try:
            db = get_db_connection()
            cur = db.cursor(dictionary=True)
            # Use case-insensitive username lookup to avoid mismatches from casing
            cur.execute("SELECT id, username, password_hash, role FROM users WHERE LOWER(username)=%s", (username.lower(),))
            user = cur.fetchone()
            cur.close()
            db.close()

            if user:
                logging.info(f"User lookup succeeded for username (normalized): {username}")
                # Be defensive: ensure password_hash is a string before passing to check_password_hash
                pw_hash = user.get('password_hash') or ''
                try:
                    password_match = check_password_hash(pw_hash, password)
                except Exception:
                    logging.error(f"Password hash check failed for user {username}: {traceback.format_exc()}")
                    password_match = False
                logging.info(f"Password match result: {password_match}")

                if password_match:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    # Normalize legacy 'stakeholder' role into 'manager'
                    normalized_role = 'manager' if user.get('role') == 'stakeholder' else user.get('role')
                    session['role'] = normalized_role
                    logging.info(f"User {username} logged in successfully with role: {normalized_role}")
                    return redirect(url_for('dashboard', role=normalized_role))
                else:
                    logging.warning(f"Password mismatch for user {username}")
            else:
                logging.warning(f"User {username} not found in database")
                
            flash("Invalid username or password", "danger")
        except Exception as e:
            logging.error(f"Login error: {traceback.format_exc()}")
            flash("An error occurred during login", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard/<role>')
@login_required
def dashboard(role):
    # only allow users to open the dashboard that matches their role,
    # but stakeholders might want to view others depending on privileges; adjust as needed
    if role != session.get('role'):
        # simple restriction: only role owner can view their dashboard
        flash("You can only access your own role dashboard.", "warning")
        return redirect(url_for('dashboard', role=session.get('role')))

    # Load sample KPIs and pass to template
    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    # Example: total revenue today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cur.execute("SELECT IFNULL(SUM(total_amount),0) as revenue FROM orders WHERE order_time >= %s", (today_start,))
    revenue_today = cur.fetchone()['revenue']

    # Example: top 5 items (by qty)
    cur.execute("""
        SELECT i.name, SUM(oi.qty) as qty_sold
        FROM order_items oi
        JOIN items i ON i.id = oi.item_id
        GROUP BY oi.item_id
        ORDER BY qty_sold DESC
        LIMIT 5
    """)
    top_items = cur.fetchall()

    # Example: low stock count (for inventory manager)
    low_stock_count = 0
    if session.get('role') == 'inventory':
        cur.execute("SELECT COUNT(*) as cnt FROM inventory WHERE quantity <= reorder_level")
        low_stock_count = cur.fetchone()['cnt']

    cur.close()
    db.close()

    # Render role-specific template; create templates/dashboards/<role>.html
    return render_template(f'dashboards/{role}.html',
                           revenue_today=revenue_today,
                           top_items=top_items,
                           low_stock_count=low_stock_count)

# ----- API ENDPOINTS for Charts / AJAX -----
@app.route('/api/kpi/revenue_range')
@login_required
def api_revenue_range():
    # returns daily revenue for last N days for Chart.js
    days = int(request.args.get('days', 14))
    end = datetime.now()
    start = end - timedelta(days=days-1)
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
      SELECT DATE(order_time) as dt, IFNULL(SUM(total_amount),0) as revenue
      FROM orders
      WHERE order_time BETWEEN %s AND %s
      GROUP BY DATE(order_time)
      ORDER BY DATE(order_time)
    """, (start, end))
    rows = cur.fetchall()
    cur.close()
    db.close()

    # Build dict of date -> revenue for continual series
    series = {}
    for r in rows:
        series[r[0].isoformat()] = float(r[1])

    labels = []
    data = []
    for i in range(days):
        day = (start + timedelta(days=i)).date()
        labels.append(day.isoformat())
        data.append(series.get(day.isoformat(), 0.0))

    return jsonify({'labels': labels, 'data': data})

@app.route('/api/top-items')
@login_required
def api_top_items():
    limit = int(request.args.get('limit', 5))
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("""
      SELECT i.name, SUM(oi.qty) as qty
      FROM order_items oi
      JOIN items i ON i.id = oi.item_id
      GROUP BY oi.item_id
      ORDER BY qty DESC
      LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(rows)


@app.route('/api/staff/performance')
@login_required
def api_staff_performance():
    """Return basic staff performance metrics. If DB tables for time tracking don't exist,
    we return lightweight defaults per user so dashboards can render.
    """
    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users")
        users = cur.fetchall()
        cur.close()
        db.close()

        # Build performance mock values that are safe if no time-tracking exists
        staff = []
        for u in users:
            worked_hours = 0
            scheduled_hours = 8
            tasks_completed = 0
            # If there is a shift_logs or time_entries table, we could compute real values here.
            staff.append({
                'id': u['id'],
                'name': u['username'],
                'role': u['role'],
                'worked_hours': worked_hours,
                'scheduled_hours': scheduled_hours,
                'tasks_completed': tasks_completed,
                'efficiency_pct': 0
            })

        return jsonify({'staff': staff, 'generated_at': datetime.now().isoformat()})
    except Exception as e:
        logging.error(f"Failed to fetch staff performance: {e}")
        return jsonify({'staff': []}), 200


@app.route('/api/shop/details')
@login_required
def api_shop_details():
    """Return basic shop metadata for the manager dashboard."""
    try:
        db = get_db_connection()
        cur = db.cursor()
        # inventory count (if inventory table exists)
        try:
            cur.execute("SELECT COUNT(*) FROM inventory")
            inventory_count = cur.fetchone()[0]
        except Exception:
            inventory_count = None

        # staff count
        try:
            cur.execute("SELECT COUNT(*) FROM users")
            staff_count = cur.fetchone()[0]
        except Exception:
            staff_count = None

        cur.close()
        db.close()

        shop = {
            'name': os.getenv('SHOP_NAME', 'Chaa Choo Café'),
            'address': os.getenv('SHOP_ADDRESS', 'Local Street, Your City'),
            'open_hours': os.getenv('SHOP_HOURS', '08:00 - 22:00'),
            'staff_count': staff_count,
            'inventory_count': inventory_count
        }
        return jsonify(shop)
    except Exception as e:
        logging.error(f"Failed to fetch shop details: {e}")
        return jsonify({'name': os.getenv('SHOP_NAME', 'Chaa Choo Café')}), 200


@app.route('/api/inventory/alerts')
@login_required
def api_inventory_alerts():
    """Return inventory alerts: items below reorder level and a simple efficiency metric."""
    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, sku, name, quantity, reorder_level FROM inventory ORDER BY quantity ASC LIMIT 100")
        rows = cur.fetchall()
        cur.close()
        db.close()

        low = [r for r in rows if r.get('quantity') is not None and r.get('reorder_level') is not None and r['quantity'] <= r['reorder_level']]
        total = len(rows)
        low_count = len(low)
        efficiency = 100 if total == 0 else max(0, round((1 - (low_count / total)) * 100, 1))

        return jsonify({'alerts': low, 'low_count': low_count, 'total_tracked': total, 'efficiency_pct': efficiency})
    except Exception as e:
        logging.error(f"Failed to fetch inventory alerts: {e}")
        return jsonify({'alerts': [], 'low_count': 0, 'total_tracked': 0, 'efficiency_pct': 100}), 200

@app.route('/api/items')
@login_required
def api_items():
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, category, price FROM items ORDER BY category, name")
    items = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(items)

# ----- PUBLIC API: Items endpoint (for order page) -----
@app.route('/api/public/items')
def api_public_items():
    """Public endpoint to fetch menu items (no login required)."""
    # If an authored JSON menu exists, serve it (includes images, descriptions)
    json_path = os.path.join(app.root_path, 'data', 'menu.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                menu = json.load(f)
            items = []
            for cat in menu.get('categories', []):
                for it in cat.get('items', []):
                    items.append({'id': it.get('id'), 'name': it.get('name'), 'category': cat.get('label'), 'price': it.get('price'), 'image': it.get('image'), 'description': it.get('description'), 'tags': it.get('tags', []), 'veg': it.get('veg', True)})
            return jsonify(items)
        except Exception as e:
            logging.error(f"Failed to load menu.json: {e}")

    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, name, category, price FROM items ORDER BY category, name")
        items = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(items)
    except Exception as e:
        logging.error(f"Failed to fetch items: {e}")
        return jsonify({'error': 'Failed to fetch items'}), 500

# ----- POS / Order creation (simple) -----
@app.route('/order/create', methods=['POST'])
@login_required
@role_required('receptionist', 'manager', 'chief')  # receptionists create orders; managers or chief may also create orders if needed
def create_order():
    """
    Expected JSON body:
    {
      "items": [{"item_id": 1, "qty":2}, ...],
      "cashier": "alice",
      "simulate_payment": true
    }
    """
    payload = request.get_json()
    if not payload or 'items' not in payload:
        return jsonify({"error": "Invalid payload"}), 400

    items = payload['items']
    cashier = payload.get('cashier', session.get('username', 'walkin'))
    simulate_payment = payload.get('simulate_payment', True)

    # calculate total and insert order + order_items; update inventory movements (very basic)
    db = get_db_connection()
    cur = db.cursor()

    try:
        # Build list of unique item IDs requested
        try:
            item_ids_list = [int(i['item_id']) for i in items]
        except Exception:
            return jsonify({'error': 'invalid_item_id'}), 400

        uniq_ids = list(dict.fromkeys(item_ids_list))
        if not uniq_ids:
            return jsonify({'error': 'no_items_provided'}), 400

        # Query prices for all requested items
        placeholders = ','.join(['%s'] * len(uniq_ids))
        cur.execute(f"SELECT id, price FROM items WHERE id IN ({placeholders})", tuple(uniq_ids))
        rows = cur.fetchall()
        price_map = {row[0]: float(row[1]) for row in rows}

        # Detect missing items
        missing = [i for i in uniq_ids if i not in price_map]
        if missing:
            cur.close(); db.close()
            return jsonify({'error': 'item_not_found', 'missing': missing}), 400

        # Compute total using fetched prices and requested quantities
        total = 0.0
        for it in items:
            iid = int(it['item_id'])
            qty = int(it.get('qty', 1))
            total += price_map.get(iid, 0.0) * qty

        # Start transactional insert
        # Insert order
        cur.execute("INSERT INTO orders (order_time, total_amount, cashier, status) VALUES (%s,%s,%s,%s)",
                    (datetime.now(), total, cashier, 'new'))
        order_id = cur.lastrowid

        # Insert order items
        for it in items:
            iid = int(it['item_id'])
            qty = int(it.get('qty', 1))
            price = price_map.get(iid, 0.0)
            cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                        (order_id, iid, qty, price))

        # Insert initial history record (best-effort)
        try:
            cur.execute("INSERT INTO order_history (order_id, old_status, new_status, changed_by, notes) VALUES (%s,%s,%s,%s,%s)",
                        (order_id, None, 'new', session.get('user_id'), f'Order created by {cashier}'))
        except Exception:
            logging.debug('order_history insert skipped or failed: ' + traceback.format_exc())

        # Optionally update inventory quantities if inventory schema supports item_id/quantity
        try:
            schema = get_table_schema(['inventory'])
            inv_cols = [c['column'] for c in (schema.get('inventory') or [])]
            if 'item_id' in inv_cols and 'quantity' in inv_cols:
                for it in items:
                    iid = int(it['item_id'])
                    qty = int(it.get('qty', 1))
                    try:
                        cur.execute("UPDATE inventory SET quantity = GREATEST(0, quantity - %s) WHERE item_id = %s", (qty, iid))
                    except Exception:
                        logging.debug('Failed to update inventory for item %s: %s' % (iid, traceback.format_exc()))
        except Exception:
            logging.debug('Inventory update skipped: ' + traceback.format_exc())

        # Set final status if payment simulated
        status = 'served' if simulate_payment else 'new'
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))

        db.commit()
        cur.close()
        db.close()

        return jsonify({"order_id": order_id, "total": total, "status": status}), 201
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logging.error('Order creation failed: ' + traceback.format_exc())
        try:
            cur.close()
            db.close()
        except Exception:
            pass
        return jsonify({'error': 'order_creation_failed', 'details': str(e)}), 500


# ----- MANAGER: create user UI -----
@app.route('/manager/create_user', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def manager_create_user():
    """Allow `manager` (merged stakeholder/manager) to create users with roles:
    'chief' (cook), 'receptionist', 'inventory', 'manager'.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'receptionist')

        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('create_user.html')

        if role not in ('chief', 'receptionist', 'inventory', 'manager'):
            flash('Invalid role selected', 'danger')
            return render_template('create_user.html')

        pw_hash = generate_password_hash(password)
        db = get_db_connection()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
                        (username, pw_hash, role))
            db.commit()
        except mysql.connector.errors.IntegrityError:
            flash('User already exists', 'warning')
            cur.close()
            db.close()
            return render_template('create_user.html')

        cur.close()
        db.close()
        flash(f'User {username} created with role {role}', 'success')
        return redirect(url_for('dashboard', role='manager'))

    return render_template('create_user.html')


# ----- MANAGER: Users management endpoints -----
@app.route('/api/manager/users', methods=['GET'])
@login_required
@role_required('manager')
def api_manager_users_list():
    """Return list of users (id, username, role) for manager UI."""
    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users ORDER BY role, username")
        rows = cur.fetchall()
        cur.close()
        db.close()
        return jsonify({'users': rows}), 200
    except Exception:
        logging.error('Failed to fetch users:\n' + traceback.format_exc())
        return jsonify({'users': []}), 200


@app.route('/api/manager/users', methods=['POST'])
@login_required
@role_required('manager')
def api_manager_users_create():
    """Create a new user via JSON body: {username, password, role} Returns JSON."""
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip().lower()
        password = data.get('password') or ''
        role = data.get('role') or 'receptionist'

        if not username or not password:
            return jsonify({'error': 'username_and_password_required'}), 400
        if role not in ('chief', 'receptionist', 'inventory', 'manager'):
            return jsonify({'error': 'invalid_role'}), 400

        pw_hash = generate_password_hash(password)
        db = get_db_connection()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
                        (username, pw_hash, role))
            db.commit()
            user_id = cur.lastrowid
        except mysql.connector.errors.IntegrityError:
            cur.close(); db.close()
            return jsonify({'error': 'user_exists'}), 409

        cur.close(); db.close()
        return jsonify({'status': 'created', 'id': user_id, 'username': username, 'role': role}), 201
    except Exception:
        logging.error('Failed to create user:\n' + traceback.format_exc())
        return jsonify({'error': 'exception'}), 500


@app.route('/manager/users', methods=['GET'])
@login_required
@role_required('manager')
def manager_users_page():
    """Server-rendered users management page (no JS required)."""
    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users ORDER BY role, username")
        users = cur.fetchall()
        cur.close()
        db.close()
        return render_template('manager_users.html', users=users)
    except Exception:
        logging.error('Failed to render manager users page:\n' + traceback.format_exc())
        flash('Failed to load users', 'danger')
        return redirect(url_for('dashboard', role='manager'))


@app.route('/manager/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('manager')
def manager_users_delete(user_id):
    """Server-side deletion to avoid JS. Prevent deleting self or managers."""
    try:
        logging.info(f"manager_users_delete called by user_id={session.get('user_id')} target_user_id={user_id}")
        if session.get('user_id') == user_id:
            flash('Cannot delete the currently logged-in user', 'warning')
            return redirect(url_for('manager_users_page'))
        
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            cur.close(); db.close()
            flash('User not found', 'warning')
            return redirect(url_for('manager_users_page'))
        
        # If target is a manager, ensure we won't delete the last remaining manager
        if user.get('role') == 'manager':
            cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='manager'")
            mgr_row = cur.fetchone()
            try:
                mgr_cnt = int(mgr_row.get('cnt', 0) if isinstance(mgr_row, dict) else (mgr_row[0] if mgr_row else 0))
            except Exception:
                mgr_cnt = 0
        
            if mgr_cnt <= 1:
                cur.close(); db.close()
                flash('Cannot delete the last remaining manager account', 'warning')
                return redirect(url_for('manager_users_page'))
        
        try:
            # First, nullify references from order_history.changed_by to avoid FK constraint
            try:
                cur.execute("UPDATE order_history SET changed_by = NULL WHERE changed_by = %s", (user_id,))
            except Exception:
                logging.debug('Could not nullify order_history.changed_by (may not exist or be nullable)')
        
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            deleted = cur.rowcount
            db.commit()
        except mysql.connector.Error as db_err:
            # If deletion still fails due to FK constraints, fall back to anonymize to preserve integrity
            logging.warning(f"DB error deleting user {user_id}: {db_err}; attempting anonymize fallback")
            try:
                import time, uuid
                from werkzeug.security import generate_password_hash
                new_username = f"deleted_user_{user_id}_{int(time.time())}"
                new_pw = generate_password_hash(uuid.uuid4().hex)
                cur.execute("UPDATE users SET username=%s, role=%s, password_hash=%s WHERE id=%s",
                            (new_username, 'disabled', new_pw, user_id))
                db.commit()
                cur.close(); db.close()
                flash('User could not be deleted due to related records; account anonymized and disabled', 'warning')
                return redirect(url_for('manager_users_page'))
            except Exception:
                logging.error(f"Anonymize fallback failed for user {user_id}: {traceback.format_exc()}")
                cur.close(); db.close()
                flash('Failed to delete user due to database constraints', 'danger')
                return redirect(url_for('manager_users_page'))
        
        cur.close(); db.close()
        logging.info(f"manager_users_delete deleted rows={deleted} for user_id={user_id}")
        flash(f"Deleted user {user.get('username')}", 'success')
        return redirect(url_for('manager_users_page'))
    except Exception:
        logging.error('Failed to delete user:\n' + traceback.format_exc())
        flash('Failed to delete user', 'danger')
        return redirect(url_for('manager_users_page'))

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            cur.close(); db.close()
            flash('User not found', 'warning')
            return redirect(url_for('manager_users_page'))

        # If target is a manager, ensure we won't delete the last remaining manager
        if user.get('role') == 'manager':
            cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='manager'")
            mgr_row = cur.fetchone()
            try:
                mgr_cnt = int(mgr_row.get('cnt', 0) if isinstance(mgr_row, dict) else (mgr_row[0] if mgr_row else 0))
            except Exception:
                mgr_cnt = 0

            if mgr_cnt <= 1:
                cur.close(); db.close()
                flash('Cannot delete the last remaining manager account', 'warning')
                return redirect(url_for('manager_users_page'))

        try:
            # Attempt to cleanup all FK references to users.id (nullify or delete dependents), then delete user
            try:
                _cleanup_user_references(cur, db, user_id)
            except Exception:
                logging.debug('FK cleanup failed: ' + traceback.format_exc())

            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            deleted = cur.rowcount
            db.commit()
        except mysql.connector.Error as db_err:
            # If deletion still fails due to FK constraints, fall back to anonymize to preserve integrity
            logging.warning(f"DB error deleting user {user_id}: {db_err}; attempting anonymize fallback")
            try:
                import time, uuid
                from werkzeug.security import generate_password_hash
                new_username = f"deleted_user_{user_id}_{int(time.time())}"
                new_pw = generate_password_hash(uuid.uuid4().hex)
                cur.execute("UPDATE users SET username=%s, role=%s, password_hash=%s WHERE id=%s",
                            (new_username, 'disabled', new_pw, user_id))
                db.commit()
                cur.close(); db.close()
                flash('User could not be deleted due to related records; account anonymized and disabled', 'warning')
                return redirect(url_for('manager_users_page'))
            except Exception:
                logging.error(f"Anonymize fallback failed for user {user_id}: {traceback.format_exc()}")
                cur.close(); db.close()
                flash('Failed to delete user due to database constraints', 'danger')
                return redirect(url_for('manager_users_page'))

        cur.close(); db.close()
        logging.info(f"manager_users_delete deleted rows={deleted} for user_id={user_id}")
        flash(f"Deleted user {user.get('username')}", 'success')
        return redirect(url_for('manager_users_page'))
    except Exception:
        logging.error('Failed to delete user:\n' + traceback.format_exc())
        flash('Failed to delete user', 'danger')
        return redirect(url_for('manager_users_page'))


@app.route('/api/manager/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('manager')
def api_manager_users_delete(user_id):
    """Delete a user from the users table. Prevent deleting self and other managers."""
    try:
        logging.info(f"api_manager_users_delete called by user_id={session.get('user_id')} target_user_id={user_id} from {request.remote_addr}")
        # Prevent deleting self
        if session.get('user_id') == user_id:
            return jsonify({'error': 'cannot_delete_self'}), 400

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        logging.info(f"api_manager_users_delete fetched user: {user}")
        if not user:
            cur.close()
            db.close()
            return jsonify({'error': 'not_found'}), 404

        # If deleting a manager, ensure we don't delete the last manager
        if user.get('role') == 'manager':
            cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='manager'")
            mgr_cnt = cur.fetchone().get('cnt', 0)
            if mgr_cnt <= 1:
                cur.close(); db.close()
                return jsonify({'error': 'cannot_delete_last_manager'}), 400

        try:
            # Attempt to cleanup FK references (nullify or delete dependents) before deleting user
            try:
                _cleanup_user_references(cur, db, user_id)
            except Exception:
                logging.debug('FK cleanup failed: ' + traceback.format_exc())

            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            deleted = cur.rowcount
            db.commit()
            cur.close(); db.close()
            logging.info(f"Manager {session.get('username')} deleted user {user.get('username')} (id={user_id}), rows_deleted={deleted}")
            return jsonify({'status': 'deleted', 'rows_deleted': deleted}), 200
        except mysql.connector.Error as db_err:
            logging.warning(f"DB error deleting user {user_id}: {db_err}; attempting anonymize fallback")
            try:
                import time, uuid
                from werkzeug.security import generate_password_hash
                new_username = f"deleted_user_{user_id}_{int(time.time())}"
                new_pw = generate_password_hash(uuid.uuid4().hex)
                cur.execute("UPDATE users SET username=%s, role=%s, password_hash=%s WHERE id=%s",
                            (new_username, 'disabled', new_pw, user_id))
                db.commit()
                cur.close(); db.close()
                logging.info(f"User {user_id} anonymized/disabled due to FK constraints")
                return jsonify({'status': 'anonymized', 'id': user_id}), 200
            except Exception:
                logging.error(f"Anonymize fallback failed for user {user_id}: {traceback.format_exc()}")
                cur.close(); db.close()
                return jsonify({'error': 'cannot_delete'}), 500
    except Exception:
        logging.error('Failed to delete user:\n' + traceback.format_exc())
        return jsonify({'error': 'exception'}), 500


# ----- MANAGER: Orders export and clear endpoints -----
@app.route('/manager/delete_self', methods=['POST'])
@login_required
@role_required('manager')
def manager_delete_self():
    """Allow a logged-in manager to delete their own account after confirming password.
    This will remove the user row, clear the session and redirect to the public index.
    """
    logging.info(f"manager_delete_self invoked by session user_id={session.get('user_id')} (type={type(session.get('user_id'))}) from {request.remote_addr}")
    password = (request.form.get('password') or '').strip()
    if not password:
        flash('Password required to confirm account deletion', 'danger')
        return redirect(url_for('dashboard', role='manager'))

    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, password_hash FROM users WHERE id=%s", (session.get('user_id'),))
        user = cur.fetchone()
        logging.info(f"manager_delete_self fetched user from DB: {user}")
        if not user:
            cur.close(); db.close()
            flash('User not found', 'warning')
            return redirect(url_for('dashboard', role='manager'))

        if not check_password_hash(user.get('password_hash', ''), password):
            cur.close(); db.close()
            flash('Invalid password', 'danger')
            return redirect(url_for('dashboard', role='manager'))

        # Attempt to cleanup dependent FK references then proceed to delete
        try:
            _cleanup_user_references(cur, db, user['id'])
        except Exception:
            logging.debug('FK cleanup failed during self-delete: ' + traceback.format_exc())

        # Proceed to delete
        cur.execute("DELETE FROM users WHERE id=%s", (user['id'],))
        deleted_rows = cur.rowcount
        db.commit()
        cur.close(); db.close()

        logging.info(f"Manager {user.get('username')} (id={user.get('id')}) deletion attempted, rows_deleted={deleted_rows}")
        session.clear()
        # If this was an AJAX request (fetch with X-Requested-With), respond with JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'deleted', 'rows_deleted': deleted_rows}), 200

        flash('Your account has been removed', 'success')
        return redirect(url_for('index'))
    except Exception:
        logging.error('Failed to delete manager self account:\n' + traceback.format_exc())
        flash('Failed to delete account', 'danger')
        return redirect(url_for('dashboard', role='manager'))
@app.route('/api/manager/orders/export', methods=['GET'])
@login_required
@role_required('manager')
def api_manager_orders_export():
    """Export all orders with items as CSV or JSON (format param: csv or json)."""
    try:
        fmt = request.args.get('format', 'csv').lower()
        if fmt not in ('csv', 'json'):
            return jsonify({'error': 'invalid_format'}), 400

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        # Fetch all orders with items
        cur.execute("SELECT * FROM orders ORDER BY id DESC")
        orders = cur.fetchall()
        
        if fmt == 'json':
            # Fetch items for each order
            for order in orders:
                cur.execute("SELECT * FROM order_items WHERE order_id=%s", (order['id'],))
                order['items'] = cur.fetchall()
            cur.close()
            db.close()
            
            # Convert datetime objects to ISO strings
            export_data = []
            for o in orders:
                o_copy = dict(o)
                for key in o_copy:
                    if isinstance(o_copy[key], datetime):
                        o_copy[key] = o_copy[key].isoformat()
                export_data.append(o_copy)
            
            from flask import Response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return Response(
                json.dumps(export_data, ensure_ascii=False, indent=2),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename=orders_{timestamp}.json'}
            )
        else:  # csv
            # Build CSV with orders and flatten items
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            
            # Headers
            writer.writerow(['OrderID', 'CustomerName', 'CustomerPhone', 'OrderType', 'TotalAmount', 
                             'Status', 'Priority', 'OrderTime', 'ItemID', 'ItemName', 'ItemQty', 'ItemPrice'])
            
            # Write rows (one per order-item combination, or order-only if no items)
            for order in orders:
                cur.execute("SELECT * FROM order_items WHERE order_id=%s", (order['id'],))
                items = cur.fetchall()
                
                if not items:
                    # Write order without items
                    writer.writerow([
                        order.get('id'), order.get('customer_name'), order.get('customer_phone'),
                        order.get('type'), order.get('total_amount'), order.get('status'),
                        order.get('priority'), order.get('order_time'), '', '', '', ''
                    ])
                else:
                    # Write one row per item
                    for item in items:
                        writer.writerow([
                            order.get('id'), order.get('customer_name'), order.get('customer_phone'),
                            order.get('type'), order.get('total_amount'), order.get('status'),
                            order.get('priority'), order.get('order_time'),
                            item.get('item_id'), item.get('id'), item.get('qty'), item.get('price')
                        ])
            
            cur.close()
            db.close()
            
            from flask import Response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=orders_{timestamp}.csv'}
            )
    except Exception:
        logging.error('Failed to export orders:\n' + traceback.format_exc())
        return jsonify({'error': 'exception'}), 500


# NOTE: /api/manager/orders/clear endpoint removed from UI and backend for safety.
# If needed in the future, consider re-adding a restricted admin-only endpoint.


# ----- MANAGER: Menu management API (reads/writes data/menu.json and saves images) -----
def _menu_json_path():
    return os.path.join(app.root_path, 'data', 'menu.json')


def _seed_item_from_menu(item_id, cur, db):
    """If an authored menu.json contains an item with the given id, insert it
    into the `items` table so orders referencing authored IDs work.
    Returns True if an insert happened, False otherwise.
    """
    try:
        p = _menu_json_path()
        if not os.path.exists(p):
            return False
        with open(p, 'r', encoding='utf-8') as f:
            menu = json.load(f)

        # Search for matching id in menu categories
        for cat in menu.get('categories', []):
            for it in cat.get('items', []):
                try:
                    mid = int(it.get('id'))
                except Exception:
                    mid = None
                if mid == int(item_id):
                    # Insert into items table if not already present
                    name = it.get('name') or f'Item {item_id}'
                    price = float(it.get('price') or 0.0)
                    category = cat.get('label') or cat.get('id')
                    description = it.get('description') or None
                    image = it.get('image') or None
                    veg = 1 if it.get('veg', True) else 0
                    tags = ','.join(it.get('tags', [])) if isinstance(it.get('tags', []), list) else (it.get('tags') or None)
                    try:
                        cur.execute("SELECT id FROM items WHERE id=%s", (mid,))
                        if cur.fetchone():
                            return True
                        cur.execute(
                            "INSERT INTO items (id, name, price, category, description, image, tags, veg) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                            (mid, name, price, category, description, image, tags, veg)
                        )
                        db.commit()
                        return True
                    except Exception:
                        logging.debug('Failed to seed item from menu: ' + traceback.format_exc())
                        try:
                            db.rollback()
                        except Exception:
                            pass
                        return False
        return False
    except Exception:
        logging.debug('Seed-from-menu failed: ' + traceback.format_exc())
        return False

def _load_menu():
    p = _menu_json_path()
    if not os.path.exists(p):
        return {'generated_at': datetime.utcnow().isoformat() + 'Z', 'currency': 'INR', 'categories': []}
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        logging.error('Failed to load menu.json:\n' + traceback.format_exc())
        return {'generated_at': datetime.utcnow().isoformat() + 'Z', 'currency': 'INR', 'categories': []}

def _save_menu(menu):
    p = _menu_json_path()
    try:
        menu['generated_at'] = datetime.utcnow().isoformat() + 'Z'
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(menu, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        logging.error('Failed to save menu.json:\n' + traceback.format_exc())
        return False

def _allowed_image(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_IMAGE_EXT


@app.route('/api/manager/menu', methods=['GET'])
@login_required
@role_required('manager')
def api_manager_menu_get():
    """Return the authored menu JSON for manager UI."""
    logging.info(f"api_manager_menu_get invoked by user_id={session.get('user_id')} from {request.remote_addr}")
    menu = _load_menu()
    try:
        cats = len(menu.get('categories', []))
    except Exception:
        cats = 0
    logging.info(f"api_manager_menu_get returning menu with {cats} categories")
    return jsonify(menu)


@app.route('/api/manager/menu/item', methods=['DELETE'])
@login_required
@role_required('manager')
def api_manager_menu_delete_item():
    """Delete an item from the authored menu JSON by id.
    Query param: id (int)
    """
    try:
        item_id = request.args.get('id')
        if not item_id:
            return jsonify({'error': 'id_required'}), 400
        menu = _load_menu()
        removed = False
        for cat in menu.get('categories', []):
            before = len(cat.get('items', []))
            cat['items'] = [it for it in cat.get('items', []) if str(it.get('id')) != str(item_id)]
            if len(cat['items']) < before:
                removed = True
        if not removed:
            return jsonify({'error': 'not_found'}), 404
        ok = _save_menu(menu)
        if not ok:
            return jsonify({'error': 'save_failed'}), 500
        return jsonify({'status': 'deleted'}), 200
    except Exception:
        logging.error('Failed to delete menu item:\n' + traceback.format_exc())
        return jsonify({'error': 'exception'}), 500


@app.route('/api/manager/menu/item', methods=['POST'])
@login_required
@role_required('manager')
def api_manager_menu_item():
    """Add or update a menu item. Accepts form-data including an optional file field `image`.

    Fields (form-data):
      - category_id: existing category id (string) or new id
      - category_label: optional label for category
      - id: optional numeric item id (if omitted, a new id will be generated)
      - name, description, price, veg (true/false), tags (comma-separated)
      - image: optional file upload
    """
    try:
        menu = _load_menu()

        form = request.form
        category_id = (form.get('category_id') or 'uncategorized').strip()
        category_label = form.get('category_label') or category_id
        item_id = form.get('id')
        name = form.get('name', '').strip()
        description = form.get('description', '').strip()
        price = float(form.get('price') or 0)
        veg = form.get('veg', 'true').lower() in ('1', 'true', 'yes')
        tags = [t.strip() for t in (form.get('tags') or '').split(',') if t.strip()]

        # handle image file
        image_filename = None
        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename:
                filename = secure_filename(f.filename)
                if not _allowed_image(filename):
                    return jsonify({'error': 'invalid_image_type'}), 400
                # prefix timestamp to avoid collisions
                safe_name = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + filename
                dest = os.path.join(app.config['MENU_IMAGE_FOLDER'], safe_name)
                f.save(dest)
                image_filename = safe_name

        # find or create category
        category = None
        for cat in menu.get('categories', []):
            if cat.get('id') == category_id:
                category = cat
                break
        if not category:
            category = {'id': category_id, 'label': category_label, 'items': []}
            menu.setdefault('categories', []).append(category)

        # update existing item if id provided
        if item_id:
            try:
                item_id_int = int(item_id)
            except ValueError:
                return jsonify({'error': 'invalid_id'}), 400
            updated = False
            for cat in menu.get('categories', []):
                for it in cat.get('items', []):
                    if int(it.get('id')) == item_id_int:
                        it['name'] = name or it.get('name')
                        it['description'] = description or it.get('description')
                        it['price'] = price
                        it['veg'] = veg
                        it['tags'] = tags
                        if image_filename:
                            it['image'] = image_filename
                        # if category changed, move item
                        if cat.get('id') != category_id:
                            cat['items'].remove(it)
                            category['items'].append(it)
                        updated = True
                        break
                if updated:
                    break
            if not updated:
                return jsonify({'error': 'item_not_found'}), 404
        else:
            # generate new id
            max_id = 0
            for cat in menu.get('categories', []):
                for it in cat.get('items', []):
                    try:
                        max_id = max(max_id, int(it.get('id', 0)))
                    except Exception:
                        continue
            new_id = max_id + 1
            new_item = {
                'id': new_id,
                'name': name,
                'description': description,
                'price': price,
                'image': image_filename or '',
                'tags': tags,
                'veg': veg
            }
            category.setdefault('items', []).append(new_item)

        ok = _save_menu(menu)
        if not ok:
            return jsonify({'error': 'save_failed'}), 500
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logging.error('Manager menu update failed:\n' + traceback.format_exc())
        return jsonify({'error': 'exception', 'details': str(e)}), 500


# ----- ADMIN / DEV: create a test user (one-off route) -----
# NOTE: Only register the dev user creation route when running in debug mode.
# This prevents accidental use in production. Use `scripts/setup_db.py` to create
# initial users and data on the server instead.
if DEBUG:
    @app.route('/dev/create_user', methods=['POST'])
    def dev_create_user():
        """
        POST form data: username, password, role
        Development-only route: creates a user for testing when DEBUG is True.
        """
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'receptionist')
        if not username or not password:
            return "username & password required", 400
        pw_hash = generate_password_hash(password)
        db = get_db_connection()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
                        (username, pw_hash, role))
            db.commit()
        except mysql.connector.errors.IntegrityError:
            cur.close()
            db.close()
            return "user exists", 400
        cur.close()
        db.close()
        return "created", 201

    @app.route('/debug/session', methods=['GET'])
    def debug_session():
        """Debug endpoint (debug-mode only) to return current session info."""
        _require_debug()
        try:
            return jsonify({
                'session': {k: session.get(k) for k in ['user_id', 'username', 'role']},
                'cookies': dict(request.cookies),
                'remote_addr': request.remote_addr
            })
        except Exception:
            logging.error('debug_session failed:\n' + traceback.format_exc())
            return jsonify({'error': 'exception'}), 500

    @app.route('/debug/menu', methods=['GET'])
    def debug_menu():
        """Debug endpoint (debug-mode only) to return the authored menu JSON without auth."""
        _require_debug()
        try:
            menu = _load_menu()
            return jsonify(menu)
        except Exception:
            logging.error('debug_menu failed:\n' + traceback.format_exc())
            return jsonify({'error': 'exception'}), 500

# ----- ERROR HANDLING -----
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_all_exceptions(e):
    logging.error("Unhandled exception:\n" + traceback.format_exc())
    return "Internal Server Error (check error.log)", 500

# ----- NEW ORDER MANAGEMENT ENDPOINTS -----
@app.route('/api/orders', methods=['GET'])
def get_orders_api():
    """
    Retrieve all orders with their items (for dashboards).
    Returns paginated list with optional filters.
    """
    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        # Get all orders with their items
        cur.execute("""
            SELECT 
                o.id, o.customer_name, o.customer_phone, o.type, 
                o.total_amount, o.status, o.priority, 
                o.customer_notes, o.order_time, o.created_at
            FROM orders o
            ORDER BY o.created_at DESC
            LIMIT 100
        """)
        orders = cur.fetchall()
        
        # For each order, fetch its items
        for order in orders:
            cur.execute("""
                SELECT oi.item_id, oi.qty, oi.price, oi.modifiers, oi.item_status
                FROM order_items oi
                WHERE oi.order_id = %s
            """, (order['id'],))
            order['items'] = cur.fetchall()
        
        cur.close()
        db.close()
        
        return jsonify({'orders': orders}), 200
    except Exception as e:
        logging.error(f"Failed to fetch orders: {e}")
        return jsonify({'error': 'Failed to fetch orders', 'details': str(e)}), 500

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order_api():
    """
    Create a new order from API (used by homepage and receptionist).
    Expected JSON:
    {
      "customer_name": "John",
      "customer_phone": "1234567890",
      "type": "dine-in|takeaway|delivery",
      "items": [{"item_id": 1, "qty": 2, "modifiers": ["extra sugar"]}],
      "total_amount": 250.00,
      "customer_notes": "No sugar",
      "priority": "normal|rush"
    }
    """
    try:
        payload = request.get_json()
        if not payload or 'items' not in payload:
            return jsonify({"error": "Invalid payload - items required"}), 400

        customer_name = payload.get('customer_name', 'Walk-in Customer')
        customer_phone = payload.get('customer_phone', '')
        order_type = payload.get('type', 'dine-in')
        items = payload['items']
        total_amount = payload.get('total_amount', 0.0)
        customer_notes = payload.get('customer_notes', '')
        priority = payload.get('priority', 'normal')

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        # Fetch and validate all item prices first (before any inserts)
        item_prices = {}
        for item in items:
            try:
                item_id = int(item['item_id'])
            except Exception:
                cur.close(); db.close()
                return jsonify({'error': 'invalid_item_id', 'item': item.get('item_id')}), 400

            cur.execute("SELECT id, price FROM items WHERE id=%s", (item_id,))
            price_row = cur.fetchone()
            if not price_row:
                # Try to seed the item from authored menu.json before failing
                try:
                    seeded = _seed_item_from_menu(item_id, cur, db)
                except Exception:
                    seeded = False
                if seeded:
                    cur.execute("SELECT id, price FROM items WHERE id=%s", (item_id,))
                    price_row = cur.fetchone()
            if not price_row:
                cur.close(); db.close()
                return jsonify({'error': 'item_not_found', 'item_id': item_id}), 400
            item_prices[item_id] = float(price_row.get('price') or 0.0)

        # Insert order (try extended columns, fallback to minimal if needed)
        try:
            cur.execute("""
                INSERT INTO orders (customer_name, type, total_amount, status, priority, customer_notes, order_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (customer_name, order_type, total_amount, 'queued', priority, customer_notes, datetime.now()))
            order_id = cur.lastrowid

            # Insert order items (attempt extended insert, fallback if columns missing)
            for item in items:
                modifiers = json.dumps(item.get('modifiers', []))
                item_id = int(item['item_id'])
                qty = int(item.get('qty', 1))
                item_price = item_prices.get(item_id, 0.0)
                try:
                    cur.execute("""
                        INSERT INTO order_items (order_id, item_id, qty, price, modifiers, item_status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (order_id, item_id, qty, item_price, modifiers, 'queued'))
                except mysql.connector.Error:
                    cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                                (order_id, item_id, qty, item_price))

        except mysql.connector.Error as ex:
            # If extended columns do not exist yet, fall back to minimal schema inserts
            logging.warning(f"Order insert failed, falling back to minimal schema: {ex}")
            cur.execute("INSERT INTO orders (order_time, total_amount, cashier, status) VALUES (%s,%s,%s,%s)",
                        (datetime.now(), total_amount, session.get('username', 'walkin'), 'queued'))
            order_id = cur.lastrowid
            for item in items:
                item_id = int(item['item_id'])
                qty = int(item.get('qty', 1))
                item_price = item_prices.get(item_id, 0.0)
                cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                            (order_id, item_id, qty, item_price))

        db.commit()
        emit_order_update(order_id, {
            'customer_name': customer_name,
            'items_count': len(items),
            'total_amount': total_amount,
            'type': order_type,
            'status': 'queued'
        }, 'new_order')

        cur.close(); db.close()
        return jsonify({
            "order_id": order_id,
            "status": "queued",
            "total_amount": total_amount,
            "message": "Order received and queued for kitchen"
        }), 201

    except Exception as e:
        logging.error(f"Order creation error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/public/orders', methods=['POST'])
def create_public_order_api():
    """
    Public endpoint for customer-facing frontend to create orders without login.
    Same payload as /api/orders but does not require authentication.
    """
    try:
        payload = request.get_json()
        if not payload or 'items' not in payload:
            return jsonify({"error": "Invalid payload - items required"}), 400

        customer_name = payload.get('customer_name', 'Walk-in Customer')
        order_type = payload.get('type', 'dine-in')
        items = payload['items']
        total_amount = payload.get('total_amount', 0.0)
        customer_notes = payload.get('customer_notes', '')
        priority = payload.get('priority', 'normal')

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        # Fetch and validate item prices
        item_prices = {}
        for item in items:
            try:
                item_id = int(item['item_id'])
            except Exception:
                cur.close(); db.close()
                return jsonify({'error': 'invalid_item_id', 'item': item.get('item_id')}), 400

            cur.execute("SELECT id, price FROM items WHERE id=%s", (item_id,))
            price_row = cur.fetchone()
            if not price_row:
                try:
                    seeded = _seed_item_from_menu(item_id, cur, db)
                except Exception:
                    seeded = False
                if seeded:
                    cur.execute("SELECT id, price FROM items WHERE id=%s", (item_id,))
                    price_row = cur.fetchone()
            if not price_row:
                cur.close(); db.close()
                return jsonify({'error': 'item_not_found', 'item_id': item_id}), 400
            item_prices[item_id] = float(price_row.get('price') or 0.0)

        try:
            cur.execute("""
                INSERT INTO orders (customer_name, type, total_amount, status, priority, customer_notes, order_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (customer_name, order_type, total_amount, 'queued', priority, customer_notes, datetime.now()))
            order_id = cur.lastrowid

            for item in items:
                modifiers = json.dumps(item.get('modifiers', []))
                item_id = int(item['item_id'])
                qty = int(item.get('qty', 1))
                item_price = item_prices.get(item_id, 0.0)
                try:
                    cur.execute("""
                        INSERT INTO order_items (order_id, item_id, qty, price, modifiers, item_status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (order_id, item_id, qty, item_price, modifiers, 'queued'))
                except mysql.connector.Error:
                    cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                                (order_id, item_id, qty, item_price))

        except mysql.connector.Error as ex:
            logging.warning(f"Extended public order insert failed, falling back: {ex}")
            cur.execute("INSERT INTO orders (order_time, total_amount, cashier, status) VALUES (%s,%s,%s,%s)",
                        (datetime.now(), total_amount, 'public', 'queued'))
            order_id = cur.lastrowid
            for item in items:
                item_id = int(item['item_id'])
                qty = int(item.get('qty', 1))
                item_price = item_prices.get(item_id, 0.0)
                cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                            (order_id, item_id, qty, item_price))

        db.commit()
        cur.close()
        db.close()

        logging.info(f"Public order {order_id} created: {len(items)} items, ₹{total_amount}")

        emit_order_update(order_id, {
            'customer_name': customer_name,
            'items_count': len(items),
            'total_amount': total_amount,
            'type': order_type,
            'status': 'queued'
        }, 'new_order')

        return jsonify({"order_id": order_id, "status": "queued", "total_amount": total_amount}), 201

    except Exception as e:
        logging.error(f"Public order creation error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Retrieve order details with items"""
    try:
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
        order = cur.fetchone()
        
        if not order:
            cur.close()
            db.close()
            return jsonify({"error": "Order not found"}), 404
        
        cur.execute("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
        order_items = cur.fetchall()
        
        # Parse JSON modifiers
        for item in order_items:
            if item.get('modifiers'):
                item['modifiers'] = json.loads(item['modifiers'])
        
        order['items'] = order_items
        cur.close()
        db.close()
        
        return jsonify(order), 200
    except Exception as e:
        logging.error(f"Get order error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
@role_required('chief', 'receptionist', 'manager')
def update_order_status(order_id):
    """Update order status (queued → preparing → ready → served)"""
    try:
        payload = request.get_json()
        new_status = payload.get('status', 'queued')
        
        if new_status not in ['queued', 'preparing', 'ready', 'served', 'cancelled']:
            return jsonify({"error": "Invalid status"}), 400

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        # Get old status
        cur.execute("SELECT status FROM orders WHERE id=%s", (order_id,))
        result = cur.fetchone()
        if not result:
            cur.close()
            db.close()
            return jsonify({"error": "Order not found"}), 404
        
        old_status = result['status']
        
        # Update order status
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
        
        # Record in history
        cur.execute("""
            INSERT INTO order_history (order_id, old_status, new_status, changed_by, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, old_status, new_status, session.get('user_id'), f"Status updated by {session.get('username')}"))
        
        db.commit()
        cur.close()
        db.close()
        
        logging.info(f"Order {order_id}: {old_status} → {new_status}")
        
        return jsonify({"order_id": order_id, "status": new_status, "message": "Status updated"}), 200
    except Exception as e:
        logging.error(f"Update order status error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/kpis/chef', methods=['GET'])
@login_required
@role_required('chief', 'manager')
def kpis_chief():
    """Chief/kitchen KPIs: prep time, completed orders, delays"""
    try:
        range_hours = int(request.args.get('range_hours', 24))
        time_cutoff = datetime.now() - timedelta(hours=range_hours)
        
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        # Avg prep time
        cur.execute("""
            SELECT AVG(TIMESTAMPDIFF(MINUTE, prep_start, prep_end)) as avg_prep_minutes
            FROM order_items
            WHERE prep_start IS NOT NULL AND prep_end IS NOT NULL
              AND prep_end >= %s
        """, (time_cutoff,))
        result = cur.fetchone()
        avg_prep_time = result.get('avg_prep_minutes', 0) or 0
        
        # Orders completed in range
        cur.execute("""
            SELECT COUNT(DISTINCT order_id) as completed_count
            FROM order_items
            WHERE item_status = 'served' AND prep_end >= %s
        """, (time_cutoff,))
        completed = cur.fetchone()['completed_count']
        
        # Delayed orders (prep time > 20 min)
        cur.execute("""
            SELECT COUNT(DISTINCT order_id) as delayed_count
            FROM order_items
            WHERE prep_start IS NOT NULL AND prep_end IS NOT NULL
              AND TIMESTAMPDIFF(MINUTE, prep_start, prep_end) > 20
              AND prep_end >= %s
        """, (time_cutoff,))
        delayed = cur.fetchone()['delayed_count']
        
        cur.close()
        db.close()
        
        on_time_percent = ((completed - delayed) / completed * 100) if completed > 0 else 0
        
        return jsonify({
            "avg_prep_time_minutes": round(avg_prep_time, 1),
            "orders_completed": completed,
            "delayed_orders": delayed,
            "on_time_percent": round(on_time_percent, 1),
            "range_hours": range_hours
        }), 200
    except Exception as e:
        logging.error(f"Chief KPIs error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/kpis/manager', methods=['GET'])
@login_required
@role_required('manager')
def kpis_manager():
    """Manager KPIs: revenue, avg order value, category breakdown, profit"""
    try:
        range_days = int(request.args.get('range_days', 30))
        time_cutoff = datetime.now() - timedelta(days=range_days)
        
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        # Total revenue and orders
        cur.execute("""
            SELECT COUNT(*) as total_orders, IFNULL(SUM(total_amount), 0) as total_revenue
            FROM orders
            WHERE order_time >= %s
        """, (time_cutoff,))
        revenue_data = cur.fetchone()
        total_orders = revenue_data['total_orders']
        total_revenue = float(revenue_data['total_revenue'])
        
        avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0
        
        # Category breakdown
        cur.execute("""
            SELECT c.category, COUNT(*) as count, SUM(oi.price * oi.qty) as revenue
            FROM order_items oi
            JOIN items c ON oi.item_id = c.id
            WHERE oi.id IN (
                SELECT id FROM order_items WHERE order_id IN (
                    SELECT id FROM orders WHERE order_time >= %s
                )
            )
            GROUP BY c.category
            ORDER BY revenue DESC
        """, (time_cutoff,))
        category_data = cur.fetchall()
        category_breakdown = {row['category']: {
            'count': row['count'],
            'revenue': float(row['revenue'] or 0)
        } for row in category_data}
        
        cur.close()
        db.close()
        
        # Assume 30% food cost, 20% labor, rest is margin
        estimated_food_cost = total_revenue * 0.30
        gross_margin_percent = ((total_revenue - estimated_food_cost) / total_revenue * 100) if total_revenue > 0 else 0
        
        return jsonify({
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "avg_order_value": round(avg_order_value, 2),
            "gross_margin_percent": round(gross_margin_percent, 1),
            "category_breakdown": category_breakdown,
            "range_days": range_days
        }), 200
    except Exception as e:
        logging.error(f"Manager KPIs error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/kpis/receptionist', methods=['GET'])
@login_required
@role_required('receptionist', 'manager')
def kpis_receptionist():
    """Receptionist KPIs: avg wait time, queue length, orders per hour"""
    try:
        range_hours = int(request.args.get('range_hours', 24))
        time_cutoff = datetime.now() - timedelta(hours=range_hours)
        
        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        
        # Orders per hour
        cur.execute("""
            SELECT COUNT(*) / %s as orders_per_hour
            FROM orders
            WHERE order_time >= %s
        """, (range_hours, time_cutoff))
        orders_per_hour = cur.fetchone()['orders_per_hour'] or 0
        
        # Current queue (queued or preparing)
        cur.execute("""
            SELECT COUNT(*) as queue_length FROM orders
            WHERE status IN ('queued', 'preparing')
        """)
        queue_length = cur.fetchone()['queue_length']
        
        # Cancellation rate
        cur.execute("""
            SELECT COUNT(*) as cancelled_orders FROM orders
            WHERE status = 'cancelled' AND order_time >= %s
        """, (time_cutoff,))
        cancelled = cur.fetchone()['cancelled_orders']
        
        cur.execute("""
            SELECT COUNT(*) as total_orders FROM orders
            WHERE order_time >= %s
        """, (time_cutoff,))
        total_orders = cur.fetchone()['total_orders']
        cancellation_rate = (cancelled / total_orders * 100) if total_orders > 0 else 0
        
        cur.close()
        db.close()
        
        return jsonify({
            "queue_length": queue_length,
            "orders_per_hour": round(orders_per_hour, 1),
            "cancellation_rate_percent": round(cancellation_rate, 1),
            "range_hours": range_hours
        }), 200
    except Exception as e:
        logging.error(f"Receptionist KPIs error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


# ----- WEBSOCKET INFRASTRUCTURE -----
# Track connected clients by role/dashboard type
connected_dashboards = {
    'chief': [],
    'receptionist': [],
    'inventory': [],
    'manager': [],
    'stakeholder': []
}

@socketio.on('connect')
def handle_connect():
    """Client connected - log connection"""
    user_role = session.get('role', 'unknown')
    logging.info(f"WebSocket client connected: {request.sid}, role={user_role}")
    emit('connection_response', {'data': 'Connected to Chaa Choo server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected - remove from tracking"""
    logging.info(f"WebSocket client disconnected: {request.sid}")

@socketio.on('join_dashboard')
def handle_join_dashboard(data):
    """Join a dashboard room for role-specific broadcasts"""
    dashboard = data.get('dashboard', 'chief')  # chief, receptionist, inventory, manager, stakeholder
    join_room(dashboard)
    if request.sid not in connected_dashboards.get(dashboard, []):
        connected_dashboards[dashboard].append(request.sid)
    logging.info(f"Client {request.sid} joined {dashboard} dashboard")
    emit('dashboard_joined', {'dashboard': dashboard})

@socketio.on('leave_dashboard')
def handle_leave_dashboard(data):
    """Leave a dashboard room"""
    dashboard = data.get('dashboard', 'chief')
    leave_room(dashboard)
    if request.sid in connected_dashboards.get(dashboard, []):
        connected_dashboards[dashboard].remove(request.sid)
    logging.info(f"Client {request.sid} left {dashboard} dashboard")

def emit_order_update(order_id, order_data, event_type='order_updated'):
    """Broadcast order update to all connected dashboards"""
    socketio.emit(event_type, {
        'order_id': order_id,
        'data': order_data,
        'timestamp': datetime.now().isoformat()
    }, room='chief')
    socketio.emit(event_type, {
        'order_id': order_id,
        'data': order_data,
        'timestamp': datetime.now().isoformat()
    }, room='receptionist')

def emit_inventory_update(ingredient_id, stock_level, status='normal'):
    """Broadcast inventory update to dashboard"""
    socketio.emit('inventory_updated', {
        'ingredient_id': ingredient_id,
        'stock_level': stock_level,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }, room='inventory')

def emit_kpi_update(dashboard_type, kpi_data):
    """Broadcast KPI updates to dashboard"""
    socketio.emit('kpi_updated', {
        'kpi_data': kpi_data,
        'dashboard': dashboard_type,
        'timestamp': datetime.now().isoformat()
    }, room=dashboard_type)


def _require_debug():
    """Helper to restrict admin diagnostics to debug mode only."""
    if not app.debug:
        from flask import abort
        abort(403, description='Diagnostics only available in debug mode')


def get_table_schema(table_names):
    """Return column metadata for given table names as a dict."""
    db = get_db_connection()
    cur = db.cursor()
    placeholders = ','.join(['%s'] * len(table_names))
    query = f"""
        SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME IN ({placeholders})
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    params = [DB_NAME] + table_names
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    db.close()

    result = {}
    for tbl, col, coltype, isnull, coldef in rows:
        result.setdefault(tbl, []).append({
            'column': col,
            'type': coltype,
            'nullable': isnull,
            'default': coldef
        })
    return result


def _cleanup_user_references(cur, db, user_id):
    """Attempt to remove or nullify foreign-key references that point to users(id).
    Strategy:
      - Query information_schema for any columns referencing users(id).
      - If the child column is nullable, SET it to NULL for rows matching the user_id.
      - If the child column is NOT nullable, DELETE the dependent rows.
    This is aggressive (may delete historical rows) but enables hard deletion of the
    user row when requested. Each operation is best-effort and failures are logged.
    """
    try:
        # Find all FK referencing users(id) in this database
        cur.execute("""
            SELECT k.TABLE_NAME as tbl, k.COLUMN_NAME as col, c.IS_NULLABLE as is_nullable
            FROM information_schema.KEY_COLUMN_USAGE k
            JOIN information_schema.COLUMNS c
              ON c.TABLE_SCHEMA = k.TABLE_SCHEMA AND c.TABLE_NAME = k.TABLE_NAME AND c.COLUMN_NAME = k.COLUMN_NAME
            WHERE k.REFERENCED_TABLE_SCHEMA = %s
              AND k.REFERENCED_TABLE_NAME = 'users'
              AND k.REFERENCED_COLUMN_NAME = 'id'
              AND k.TABLE_SCHEMA = %s
        """, (DB_NAME, DB_NAME))
        refs = cur.fetchall()
        for r in refs:
            try:
                tbl = r['tbl'] if isinstance(r, dict) else r[0]
                col = r['col'] if isinstance(r, dict) else r[1]
                is_nullable = (r['is_nullable'] if isinstance(r, dict) else r[2]) or 'NO'
                if str(is_nullable).upper() == 'YES':
                    logging.info(f"Nullifying {tbl}.{col} for user {user_id}")
                    cur.execute(f"UPDATE `{tbl}` SET `{col}` = NULL WHERE `{col}` = %s", (user_id,))
                else:
                    logging.info(f"Deleting dependent rows from {tbl} where {col}=%s", user_id)
                    cur.execute(f"DELETE FROM `{tbl}` WHERE `{col}` = %s", (user_id,))
            except Exception:
                logging.warning(f"Failed to cleanup reference on {r}: {traceback.format_exc()}")
        # Note: caller should commit when appropriate
    except Exception:
        logging.debug('Could not enumerate or cleanup FK references: ' + traceback.format_exc())


@app.route('/admin/db_schema', methods=['GET'])
def admin_db_schema():
    """Return schema details for key tables. Debug-mode only."""
    _require_debug()
    tables = ['orders', 'order_items', 'items', 'users', 'inventory', 'order_history', 'ingredients']
    try:
        schema = get_table_schema(tables)
        return jsonify({'ok': True, 'schema': schema}), 200
    except Exception as e:
        logging.error(f"DB schema diagnostics error: {traceback.format_exc()}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/admin/check_migrations', methods=['GET'])
def admin_check_migrations():
    """Check presence of expected columns and return a small report. Debug-mode only."""
    _require_debug()
    checks = {
        'orders': ['customer_name', 'customer_phone', 'type', 'customer_notes', 'priority'],
        'order_items': ['price', 'modifiers', 'item_status', 'prep_start', 'prep_end'],
        'order_history': ['order_id', 'old_status', 'new_status'],
    }
    report = {}
    try:
        schema = get_table_schema(list(checks.keys()))
        for tbl, expected_cols in checks.items():
            existing = [c['column'] for c in schema.get(tbl, [])]
            missing = [c for c in expected_cols if c not in existing]
            report[tbl] = {
                'present': existing,
                'missing': missing,
                'ok': len(missing) == 0
            }
        return jsonify({'ok': True, 'report': report}), 200
    except Exception as e:
        logging.error(f"Migration check error: {traceback.format_exc()}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ----- START -----
if __name__ == '__main__':
    # For local dev only. Use gunicorn for production.
    # Read port from environment so we can avoid conflicts during development.
    port = int(os.getenv('PORT', '8080'))
    # Use socketio.run() for WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
