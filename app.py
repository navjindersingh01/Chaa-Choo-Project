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

# Configure logging
log_file = os.getenv("LOG_FILE", "error.log")
log_level = logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO
logging.basicConfig(
    filename=log_file,
    level=log_level,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from functools import wraps


# ----- CONFIG -----
# Read all configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "11111111")
DB_NAME = os.getenv("DB_NAME", "cafe_ca3")
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret_in_production")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
FLASK_ENV = os.getenv("FLASK_ENV", "development")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['DEBUG'] = DEBUG
app.config['ENV'] = FLASK_ENV
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JSON_SORT_KEYS'] = False
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
            cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
            cur.close()
            db.close()
            
            if user:
                logging.info(f"User {username} found in database")
                password_match = check_password_hash(user['password_hash'], password)
                logging.info(f"Password match result: {password_match}")

                if password_match:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    # Normalize legacy 'stakeholder' role into 'manager'
                    normalized_role = 'manager' if user['role'] == 'stakeholder' else user['role']
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

    # fetch item prices and costs
    item_ids = tuple(set([int(i['item_id']) for i in items]))
    format_ids = "(" + ",".join(["%s"] * len(item_ids)) + ")"
    cur.execute(f"SELECT id, price FROM items WHERE id IN {format_ids}", item_ids)
    price_map = {row[0]: float(row[1]) for row in cur.fetchall()}

    total = 0.0
    for it in items:
        total += price_map.get(int(it['item_id']), 0.0) * int(it.get('qty', 1))

    # create order
    cur.execute("INSERT INTO orders (order_time, total_amount, cashier, status) VALUES (%s,%s,%s,%s)",
                (datetime.now(), total, cashier, 'new'))
    order_id = cur.lastrowid

    # insert order items
    for it in items:
        cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                    (order_id, int(it['item_id']), int(it.get('qty', 1)), price_map.get(int(it['item_id']), 0.0)))

    # Optionally set status to 'served' if simulated payment succeeded
    status = 'served' if simulate_payment else 'new'
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"order_id": order_id, "total": total, "status": status}), 201


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
        if user.get('role') == 'manager':
            cur.close(); db.close()
            flash('Cannot delete another manager', 'warning')
            return redirect(url_for('manager_users_page'))

        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        db.commit()
        cur.close(); db.close()
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
        # Prevent deleting self
        if session.get('user_id') == user_id:
            return jsonify({'error': 'cannot_delete_self'}), 400

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, username, role FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            cur.close()
            db.close()
            return jsonify({'error': 'not_found'}), 404

        # Prevent deleting another manager (keep at least managers safe)
        if user.get('role') == 'manager':
            cur.close()
            db.close()
            return jsonify({'error': 'cannot_delete_manager'}), 403

        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        db.commit()
        cur.close()
        db.close()
        logging.info(f"Manager {session.get('username')} deleted user {user.get('username')} (id={user_id})")
        return jsonify({'status': 'deleted'}), 200
    except Exception:
        logging.error('Failed to delete user:\n' + traceback.format_exc())
        return jsonify({'error': 'exception'}), 500


# ----- MANAGER: Orders export and clear endpoints -----
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
    menu = _load_menu()
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

        # Fetch all item prices first (before any inserts)
        item_prices = {}
        for item in items:
            item_id = int(item['item_id'])
            price_cur = db.cursor(dictionary=True)
            price_cur.execute("SELECT price FROM items WHERE id=%s", (item_id,))
            price_row = price_cur.fetchone()
            price_cur.close()
            item_prices[item_id] = float(price_row['price']) if price_row else 0.0

        # Insert order
        cur.execute("""
            INSERT INTO orders (customer_name, type, total_amount, status, priority, customer_notes, order_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (customer_name, order_type, total_amount, 'queued', priority, customer_notes, datetime.now()))
        
        order_id = cur.lastrowid

        # Try inserting order with extended columns (if migrations applied)
        try:
            cur.execute("""
                INSERT INTO orders (customer_name, type, total_amount, status, priority, customer_notes, order_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (customer_name, order_type, total_amount, 'queued', priority, customer_notes, datetime.now()))
            order_id = cur.lastrowid

            # Insert order items (with modifiers / item_status if available)
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
                    # Fallback if order_items doesn't have modifiers/item_status/price columns
                    cur.execute("""
                        INSERT INTO order_items (order_id, item_id, qty, price)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, item_id, qty, item_price))

        except mysql.connector.Error as ex:
            # If extended columns do not exist yet, fall back to minimal schema inserts
            logging.warning(f"Extended order insert failed, falling back to minimal schema: {ex}")
            # Try minimal insert into orders (order_time, total_amount, cashier, status)
            cur.execute("INSERT INTO orders (order_time, total_amount, cashier, status) VALUES (%s,%s,%s,%s)",
                        (datetime.now(), total_amount, session.get('username', 'walkin'), 'queued'))
            order_id = cur.lastrowid

            # Insert order items with minimal columns (order_id, item_id, qty, price)
            for item in items:
                item_id = int(item['item_id'])
                qty = int(item.get('qty', 1))
                item_price = item_prices.get(item_id, 0.0)
                cur.execute("INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s,%s,%s,%s)",
                            (order_id, item_id, qty, item_price))
        emit_order_update(order_id, {
            'customer_name': customer_name,
            'items_count': len(items),
            'total_amount': total_amount,
            'type': order_type,
            'status': 'queued'
        }, 'new_order')
        
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

        # Fetch item prices
        item_prices = {}
        for item in items:
            item_id = int(item['item_id'])
            price_cur = db.cursor(dictionary=True)
            price_cur.execute("SELECT price FROM items WHERE id=%s", (item_id,))
            price_row = price_cur.fetchone()
            price_cur.close()
            item_prices[item_id] = float(price_row['price']) if price_row else 0.0

        # Try extended insert first
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
            # minimal fallback
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


import json


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
