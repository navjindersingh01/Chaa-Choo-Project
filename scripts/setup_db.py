#!/usr/bin/env python3
"""
Database setup script for Chaa Choo Café
Creates tables and inserts test data.

This script is idempotent and PythonAnywhere-friendly:
- It attempts to create the database when permitted.
- If the DB user does not have permission to create databases (common on PA),
    it will attempt to connect to the provided database and create tables there.
Usage:
    python3 scripts/setup_db.py [--seed-only]
"""

import argparse
import mysql.connector
from werkzeug.security import generate_password_hash
import os
import sys

# Load DB credentials from environment variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "11111111")
DB_NAME = os.getenv("DB_NAME", "cafe_ca3")

def create_tables(cursor):
    """Create all necessary tables"""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created 'users' table")

    # Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created 'items' table")

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount DECIMAL(10, 2) NOT NULL,
            cashier VARCHAR(50),
            status ENUM('new', 'served', 'completed', 'cancelled') DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created 'orders' table")

    # Order items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            item_id INT NOT NULL,
            qty INT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    print("✓ Created 'order_items' table")

    # Inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT NOT NULL,
            quantity INT NOT NULL,
            reorder_level INT DEFAULT 10,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    print("✓ Created 'inventory' table")


def insert_test_users(cursor):
    """Insert test users for different roles"""
    
    test_users = [
        ('alice', 'password', 'chief'),
        ('bob', 'password', 'receptionist'),
        ('charlie', 'password', 'inventory'),
        ('diana', 'password', 'manager'),
        ('eve', 'password', 'manager'),
    ]

    for username, password, role in test_users:
        try:
            pw_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, pw_hash, role)
            )
            print(f"✓ Created user: {username} (role: {role})")
        except mysql.connector.errors.IntegrityError:
            print(f"  ⚠ User {username} already exists, skipping...")


def insert_sample_items(cursor):
    """Insert sample café items"""
    
    sample_items = [
        ('Espresso', 'Coffee', 50.00, 'Strong black coffee'),
        ('Cappuccino', 'Coffee', 80.00, 'Coffee with steamed milk'),
        ('Latte', 'Coffee', 90.00, 'Creamy coffee with milk'),
        ('Americano', 'Coffee', 60.00, 'Diluted espresso'),
        ('Green Tea', 'Tea', 40.00, 'Refreshing green tea'),
        ('Black Tea', 'Tea', 40.00, 'Strong black tea'),
        ('Iced Coffee', 'Coffee', 70.00, 'Cold coffee drink'),
        ('Croissant', 'Pastry', 100.00, 'Buttery French pastry'),
        ('Muffin', 'Pastry', 80.00, 'Chocolate chip muffin'),
        ('Sandwich', 'Sandwich', 150.00, 'Veggie sandwich'),
        ('Club Sandwich', 'Sandwich', 200.00, 'Triple-decker sandwich'),
        ('Brownie', 'Pastry', 120.00, 'Chocolate brownie'),
    ]

    for name, category, price, description in sample_items:
        try:
            cursor.execute(
                "INSERT INTO items (name, category, price, description) VALUES (%s, %s, %s, %s)",
                (name, category, price, description)
            )
            print(f"✓ Added item: {name} ({category}) - ₹{price}")
        except mysql.connector.errors.IntegrityError:
            print(f"  ⚠ Item {name} already exists, skipping...")

def insert_sample_inventory(cursor):
    """Insert sample inventory data"""
    
    # Get all items
    cursor.execute("SELECT id FROM items")
    items = cursor.fetchall()
    
    for item in items:
        item_id = item[0]
        try:
            cursor.execute(
                "INSERT INTO inventory (item_id, quantity, reorder_level) VALUES (%s, %s, %s)",
                (item_id, 50, 10)
            )
        except mysql.connector.errors.IntegrityError:
            print(f"  ⚠ Inventory for item {item_id} already exists, skipping...")
    
    print(f"✓ Added inventory for {len(items)} items")

def main(seed_only=False):
    """Main setup function. If `seed_only` is True, the script will not attempt to create the database and
    will only insert seed data into the existing DB.
    """

    print("\n" + "="*60)
    print("  🔧 Chaa Choo Database Setup")
    print("="*60 + "\n")

    try:
        # Attempt to create the database if permissions allow (safe to run even when not allowed)
        try:
            admin_conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                autocommit=True,
            )
            admin_cursor = admin_conn.cursor()
            try:
                if not seed_only:
                    admin_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
                    print(f"✓ Database '{DB_NAME}' ready or already exists\n")
            except mysql.connector.Error as create_err:
                # Not fatal; may not have privileges (PythonAnywhere users commonly hit this)
                print(f"⚠ Could not create database (may lack privileges): {create_err}")
                print("⚠ Will attempt to connect to the provided database and create tables there.")
            finally:
                try:
                    admin_cursor.close()
                    admin_conn.close()
                except Exception:
                    pass
        except mysql.connector.Error as conn_err:
            print(f"\n❌ Cannot connect to MySQL server at {DB_HOST}: {conn_err}")
            return False

        # Connect to the target database
        try:
            db = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
        except mysql.connector.Error as db_conn_err:
            print(f"\n❌ Failed to connect to database '{DB_NAME}': {db_conn_err}")
            print("If you're on PythonAnywhere, create the database from the Databases tab and then set DB_HOST, DB_USER, DB_NAME accordingly.")
            return False

        cursor = db.cursor()

        # Create tables (idempotent)
        print("Creating tables...")
        create_tables(cursor)

        if not seed_only:
            print("\nInserting test users...")
            insert_test_users(cursor)

            print("\nInserting sample items...")
            insert_sample_items(cursor)

            print("\nSetting up inventory...")
            insert_sample_inventory(cursor)

        db.commit()

        print("\n" + "="*60)
        print("  ✅ Database setup complete!")
        print("="*60)
        print("\n📝 Test Credentials:")
        print("   Username: alice    | Password: password (Chief)")
        print("   Username: bob      | Password: password (Receptionist)")
        print("   Username: charlie  | Password: password (Inventory)")
        print("   Username: diana    | Password: password (Manager)")
        print("   Username: eve      | Password: password (Manager)")
        print("\n🔗 Access the app at: http://localhost:8080\n")

        cursor.close()
        db.close()

    except mysql.connector.Error as err:
        print(f"\n❌ Database Error: {err}")
        return False
    except Exception as err:
        print(f"\n❌ Error: {err}")
        return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup Chaa Choo database and seed sample data')
    parser.add_argument('--seed-only', action='store_true', help='Only insert seed data; do not attempt to create the database')
    args = parser.parse_args()
    success = main(seed_only=args.seed_only)
    sys.exit(0 if success else 1)
