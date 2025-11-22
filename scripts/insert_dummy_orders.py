"""
Insert dummy order data into the Chaa Choo database for dashboard demonstration.
Run with: ./venv/bin/python insert_dummy_orders.py
"""
import mysql.connector
import os
from datetime import datetime, timedelta
import random

# Load DB credentials from environment variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "11111111")
DB_NAME = os.getenv("DB_NAME", "cafe_ca3")

def insert_dummy_orders():
    """Insert sample orders for the last 14 days"""
    try:
        cnx = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, auth_plugin='mysql_native_password'
        )
        cur = cnx.cursor(dictionary=True)
        
        # Get all items
        cur.execute("SELECT id, price FROM items")
        items = cur.fetchall()
        item_ids = [item['id'] for item in items]
        item_prices = {item['id']: item['price'] for item in items}
        
        print(f"Found {len(items)} menu items")
        
        # Get cashiers (receptionists and chief)
        cur.execute("SELECT username FROM users WHERE role IN ('receptionist', 'chief')")
        cashiers = [row['username'] for row in cur.fetchall()]
        print(f"Found cashiers: {cashiers}")
        
        # Insert orders for the last 14 days
        base_date = datetime.now() - timedelta(days=14)
        orders_inserted = 0
        order_items_inserted = 0
        
        for day_offset in range(14):
            # Generate 3-8 orders per day
            num_orders = random.randint(3, 8)
            
            for _ in range(num_orders):
                # Random time during business hours (8 AM to 6 PM)
                hour = random.randint(8, 18)
                minute = random.randint(0, 59)
                order_time = base_date + timedelta(days=day_offset, hours=hour, minutes=minute)
                
                # Generate order with 1-4 items
                order_items = random.sample(items, random.randint(1, 4))
                total_amount = sum(
                    item['price'] * random.randint(1, 3)
                    for item in order_items
                )
                
                cashier = random.choice(cashiers)
                
                # Insert order
                cur.execute(
                    "INSERT INTO orders (order_time, total_amount, cashier, status) VALUES (%s, %s, %s, %s)",
                    (order_time, total_amount, cashier, 'completed')
                )
                order_id = cur.lastrowid
                orders_inserted += 1
                
                # Insert order items
                for item in order_items:
                    qty = random.randint(1, 3)
                    cur.execute(
                        "INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s, %s, %s, %s)",
                        (order_id, item['id'], qty, item['price'])
                    )
                    order_items_inserted += 1
        
        cnx.commit()
        cur.close()
        cnx.close()
        
        print(f"\n✅ Dummy data inserted successfully!")
        print(f"   • Orders inserted: {orders_inserted}")
        print(f"   • Order items inserted: {order_items_inserted}")
        print(f"\nDashboard will now show:")
        print(f"   • Revenue analytics for last 14 days")
        print(f"   • Top selling items chart")
        print(f"   • Total revenue calculations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("  📊 Chaa Choo - Insert Dummy Order Data")
    print("=" * 60 + "\n")
    insert_dummy_orders()
