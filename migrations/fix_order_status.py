"""
Migration: Fix orders.status ENUM to include all necessary statuses
Run with: ./venv/bin/python migrations/fix_order_status.py
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
    
    print("Updating orders.status ENUM...")
    
    # Change ENUM to VARCHAR to support all statuses flexibly
    cur.execute("ALTER TABLE orders MODIFY COLUMN status VARCHAR(50) DEFAULT 'queued'")
    print("✓ Changed status column to VARCHAR(50)")
    
    cnx.commit()
    cur.close()
    cnx.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
