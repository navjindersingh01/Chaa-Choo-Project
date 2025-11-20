"""
Migration: Add customer details to orders table
Run with: ./venv/bin/python migrations/add_customer_fields.py
"""
import mysql.connector
import os

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "11111111")
DB_NAME = os.getenv("DB_NAME", "cafe_ca3")

try:
    cnx = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, auth_plugin='mysql_native_password'
    )
    cur = cnx.cursor()
    
    print("Adding customer fields to orders table...")
    
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN customer_name VARCHAR(255) AFTER id")
        print("✓ Added customer_name")
    except:
        print("ℹ customer_name exists")
    
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN customer_phone VARCHAR(20) AFTER customer_name")
        print("✓ Added customer_phone")
    except:
        print("ℹ customer_phone exists")
    
    cnx.commit()
    cur.close()
    cnx.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
