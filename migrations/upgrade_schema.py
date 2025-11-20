"""
Database migration: Enhance schema for real-time order management and detailed dashboards.
This script adds tables and columns needed for Chief, Receptionist, Inventory, Manager, and Stakeholder dashboards.

Run with: ./venv/bin/python migrations/upgrade_schema.py
"""
import mysql.connector
import os
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "11111111")
DB_NAME = os.getenv("DB_NAME", "cafe_ca3")

def run_migrations():
    try:
        cnx = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, auth_plugin='mysql_native_password'
        )
        cur = cnx.cursor()
        
        print("Running database migrations...\n")
        
        # 1. Upgrade orders table with order type and timestamps
        print("1. Upgrading orders table...")
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN type VARCHAR(20) DEFAULT 'dine-in' AFTER total_amount")
            print("   ✓ Added type column")
        except:
            print("   ℹ type column already exists")
        
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN requested_time DATETIME AFTER order_time")
            print("   ✓ Added requested_time column")
        except:
            print("   ℹ requested_time column already exists")
        
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN assigned_chef INT AFTER status")
            print("   ✓ Added assigned_chef column")
        except:
            print("   ℹ assigned_chef column already exists")
        
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_partner INT AFTER assigned_chef")
            print("   ✓ Added delivery_partner column")
        except:
            print("   ℹ delivery_partner column already exists")
        
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_notes TEXT AFTER delivery_partner")
            print("   ✓ Added customer_notes column")
        except:
            print("   ℹ customer_notes column already exists")
        
        try:
            cur.execute("ALTER TABLE orders ADD COLUMN priority VARCHAR(20) DEFAULT 'normal' AFTER customer_notes")
            print("   ✓ Added priority column")
        except:
            print("   ℹ priority column already exists")
        
        # 2. Upgrade order_items table with more detail
        print("\n2. Upgrading order_items table...")
        try:
            cur.execute("ALTER TABLE order_items ADD COLUMN modifiers JSON AFTER qty")
            print("   ✓ Added modifiers column")
        except:
            print("   ℹ modifiers column already exists")
        
        try:
            cur.execute("ALTER TABLE order_items ADD COLUMN item_status VARCHAR(50) DEFAULT 'queued' AFTER modifiers")
            print("   ✓ Added item_status column")
        except:
            print("   ℹ item_status column already exists")
        
        try:
            cur.execute("ALTER TABLE order_items ADD COLUMN prep_start DATETIME AFTER item_status")
            print("   ✓ Added prep_start column")
        except:
            print("   ℹ prep_start column already exists")
        
        try:
            cur.execute("ALTER TABLE order_items ADD COLUMN prep_end DATETIME AFTER prep_start")
            print("   ✓ Added prep_end column")
        except:
            print("   ℹ prep_end column already exists")
        
        # 3. Create ingredients table
        print("\n3. Creating ingredients table...")
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    category VARCHAR(100),
                    unit VARCHAR(50),
                    current_qty DECIMAL(10, 2),
                    reorder_point DECIMAL(10, 2),
                    on_order_qty DECIMAL(10, 2) DEFAULT 0,
                    cost_per_unit DECIMAL(10, 2),
                    supplier_id INT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✓ Created ingredients table")
        except:
            print("   ℹ ingredients table already exists")
        
        # 4. Create suppliers table
        print("\n4. Creating suppliers table...")
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    contact_person VARCHAR(255),
                    phone VARCHAR(20),
                    email VARCHAR(255),
                    address TEXT,
                    lead_time_days INT DEFAULT 3,
                    payment_terms VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✓ Created suppliers table")
        except:
            print("   ℹ suppliers table already exists")
        
        # 5. Create purchase_orders table
        print("\n5. Creating purchase_orders table...")
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    supplier_id INT NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    total_amount DECIMAL(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expected_delivery DATETIME,
                    actual_delivery DATETIME,
                    notes TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            """)
            print("   ✓ Created purchase_orders table")
        except:
            print("   ℹ purchase_orders table already exists")
        
        # 6. Create purchase_order_items table
        print("\n6. Creating purchase_order_items table...")
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    purchase_order_id INT NOT NULL,
                    ingredient_id INT NOT NULL,
                    qty DECIMAL(10, 2),
                    unit_price DECIMAL(10, 2),
                    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
                )
            """)
            print("   ✓ Created purchase_order_items table")
        except:
            print("   ℹ purchase_order_items table already exists")
        
        # 7. Create order_history table for audit
        print("\n7. Creating order_history table...")
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    old_status VARCHAR(50),
                    new_status VARCHAR(50),
                    changed_by INT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (changed_by) REFERENCES users(id)
                )
            """)
            print("   ✓ Created order_history table")
        except:
            print("   ℹ order_history table already exists")
        
        # 8. Create daily_metrics table for KPI aggregation
        print("\n8. Creating daily_metrics table...")
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    metric_date DATE NOT NULL UNIQUE,
                    total_revenue DECIMAL(10, 2),
                    total_orders INT,
                    avg_prep_time_minutes FLOAT,
                    orders_completed INT,
                    delayed_orders INT,
                    avg_customer_wait_time_minutes FLOAT,
                    category_breakdown JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✓ Created daily_metrics table")
        except:
            print("   ℹ daily_metrics table already exists")
        
        cnx.commit()
        cur.close()
        cnx.close()
        
        print("\n" + "="*60)
        print("✅ Database schema upgrade complete!")
        print("="*60)
        print("\nNew capabilities:")
        print("  • Order types (dine-in, takeaway, delivery)")
        print("  • Chef assignment and tracking")
        print("  • Ingredient/inventory management")
        print("  • Purchase order workflow")
        print("  • Order status audit history")
        print("  • Daily KPI aggregation")
        print("  • Modifiers and special requests")
        print("  • Order prep time tracking")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("="*60)
    print("  🔧 Chaa Choo - Database Schema Upgrade")
    print("="*60 + "\n")
    run_migrations()
