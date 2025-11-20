#!/usr/bin/env python3
"""Fix order_items.price to have a default value"""

import mysql.connector
from mysql.connector import Error
import os

try:
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', '11111111'),
        database=os.getenv('DB_NAME', 'cafe_ca3')
    )
    
    cur = db.cursor()
    
    # Add default value to price column
    cur.execute("""
        ALTER TABLE order_items 
        MODIFY COLUMN price DECIMAL(10, 2) DEFAULT 0.00 NOT NULL
    """)
    
    db.commit()
    print("✅ order_items.price column updated with DEFAULT 0.00")
    
    cur.close()
    db.close()
    
except Error as e:
    print(f"❌ Error: {e}")
    exit(1)
