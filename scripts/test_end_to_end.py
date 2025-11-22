#!/usr/bin/env python3
"""
End-to-End Test: Order Flow from Homepage → Order Page → Database → Chief Dashboard
"""

import requests
import json
import time
import mysql.connector
from datetime import datetime

BASE_URL = "http://127.0.0.1:8081"

def test_public_items():
    """Test 1: Get menu items (no login required)"""
    print("\n" + "="*70)
    print("TEST 1: Public Menu Items Endpoint")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/public/items")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        items = response.json()
        print(f"✓ Retrieved {len(items)} menu items")
        print(f"  Sample: {items[0]['name']} ({items[0]['category']}) - ₹{items[0]['price']}")
        return items
    else:
        print(f"✗ Failed: {response.text}")
        return None

def test_order_creation(items):
    """Test 2: Create order via public API"""
    print("\n" + "="*70)
    print("TEST 2: Create Order (Public API)")
    print("="*70)
    
    payload = {
        "customer_name": f"Test Customer {int(time.time())}",
        "type": "dine-in",
        "items": [
            {"item_id": items[0]['id'], "qty": 2},
            {"item_id": items[1]['id'], "qty": 1}
        ],
        "total_amount": 180.00,
        "customer_notes": "Hot coffee, extra sugar"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/public/orders",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    if response.status_code == 201:
        data = response.json()
        order_id = data['order_id']
        print(f"✓ Order created successfully!")
        print(f"  Order ID: {order_id}")
        print(f"  Status: {data['status']}")
        print(f"  Total: ₹{data['total_amount']}")
        return order_id
    else:
        print(f"✗ Failed: {response.text}")
        return None

def test_db_verify(order_id):
    """Test 3: Verify order in database"""
    print("\n" + "="*70)
    print("TEST 3: Verify Order in Database")
    print("="*70)
    
    try:
        db = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="11111111",
            database="cafe_ca3"
        )
        
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        
        if order:
            print(f"✓ Order found in database!")
            print(f"  ID: {order['id']}")
            print(f"  Customer: {order.get('customer_name', 'N/A')}")
            print(f"  Status: {order['status']}")
            print(f"  Type: {order.get('type', 'N/A')}")
            print(f"  Total: ₹{order['total_amount']}")
            print(f"  Created: {order.get('order_time', 'N/A')}")
            
            cur.execute("SELECT item_id, qty, price FROM order_items WHERE order_id = %s", (order_id,))
            items = cur.fetchall()
            print(f"  Items: {len(items)} items")
            for item in items:
                print(f"    - Item {item['item_id']}: {item['qty']}x @ ₹{item['price']}")
            
            cur.close()
            db.close()
            return True
        else:
            print(f"✗ Order not found in database!")
            cur.close()
            db.close()
            return False
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_homepage_links():
    """Test 4: Verify homepage product links"""
    print("\n" + "="*70)
    print("TEST 4: Homepage Product Links")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/")
    
    if response.status_code == 200:
        html = response.text
        if 'href="{{ url_for(\'order_page\') }}"' in html or 'href="/order"' in html:
            print(f"✓ Homepage has product links to /order")
            if 'class="item-card"' in html:
                print(f"✓ Product cards present in HTML")
            if 'cursor: pointer' in html:
                print(f"✓ Product cards have cursor: pointer styling")
            return True
        else:
            print(f"✗ Homepage missing product links")
            return False
    else:
        print(f"✗ Failed to load homepage: {response.status_code}")
        return False

def test_order_page():
    """Test 5: Verify order page loads"""
    print("\n" + "="*70)
    print("TEST 5: Order Page Template")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/order")
    
    if response.status_code == 200:
        html = response.text
        checks = [
            ("Cart container", 'id="cart' in html),
            ("Checkout button", 'onclick="placeOrder()' in html),
            ("Fetch public items", 'api_public_items' in html),
            ("Order submission", '/api/public/orders' in html),
        ]
        
        all_pass = True
        for check_name, result in checks:
            if result:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name}")
                all_pass = False
        
        return all_pass
    else:
        print(f"✗ Failed to load /order page: {response.status_code}")
        return False

def test_chief_dashboard_tabs():
    """Test 6: Verify chief dashboard tabs"""
    print("\n" + "="*70)
    print("TEST 6: Chief Dashboard Tabs")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/dashboard/chief")
    
    if response.status_code == 200:
        html = response.text
        checks = [
            ("Tab navigation", 'class="tab-navigation"' in html),
            ("Overview tab", 'id="overview"' in html),
            ("Queue tab", 'id="queue"' in html),
            ("Metrics tab", 'id="metrics"' in html),
            ("Tab switching function", 'function switchTab' in html),
            ("Load metrics function", 'function loadDetailedMetrics' in html),
        ]
        
        all_pass = True
        for check_name, result in checks:
            if result:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name}")
                all_pass = False
        
        return all_pass
    else:
        print(f"✗ Failed to load chief dashboard: {response.status_code}")
        return False

if __name__ == '__main__':
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "CHAA CHOO - END-TO-END ORDER FLOW TEST" + " "*15 + "║")
    print("╚" + "="*68 + "╝")
    
    # Run all tests
    items = test_public_items()
    if not items:
        print("\n✗ Cannot proceed without menu items")
        exit(1)
    
    order_id = test_order_creation(items)
    if not order_id:
        print("\n✗ Cannot proceed without valid order")
        exit(1)
    
    db_verified = test_db_verify(order_id)
    homepage_ok = test_homepage_links()
    order_page_ok = test_order_page()
    dashboard_ok = test_chief_dashboard_tabs()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    results = {
        "✓ Order Created": order_id is not None,
        "✓ Order in Database": db_verified,
        "✓ Homepage Links": homepage_ok,
        "✓ Order Page": order_page_ok,
        "✓ Chief Dashboard Tabs": dashboard_ok,
    }
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    if all(results.values()):
        print("\n" + "🎉 "*10)
        print("ALL TESTS PASSED - ORDER FLOW IS WORKING END-TO-END!")
        print("🎉 "*10)
    else:
        print("\n" + "⚠️ "*10)
        print("SOME TESTS FAILED - SEE DETAILS ABOVE")
        print("⚠️ "*10)
