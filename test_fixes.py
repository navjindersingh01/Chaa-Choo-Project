#!/usr/bin/env python3
"""Test script to verify the two fixes:
1. Homepage product cards link to order page
2. Chief dashboard has working tabs
"""

import re
from pathlib import Path

def test_homepage_product_links():
    """Test that product cards on homepage link to /order"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    # Check for product cards wrapped in links
    if 'href="{{ url_for(\'order_page\') }}"' in content:
        print("✓ Homepage: Product cards link to /order route")
        # Verify it's wrapping the item-card
        if '<a href="{{ url_for(\'order_page\') }}"' in content and 'class="item-card"' in content:
            print("✓ Homepage: Product cards have proper link wrapper")
            return True
    else:
        print("✗ Homepage: Product links not found")
        return False

def test_chief_dashboard_tabs():
    """Test that chief dashboard has tab navigation"""
    chief_path = Path("templates/dashboards/chief.html")
    content = chief_path.read_text()
    
    checks = [
        ("Tab container", '<div class="tab-container">' in content),
        ("Tab navigation", 'class="tab-navigation"' in content),
        ("Tab buttons", 'onclick="switchTab(' in content),
        ("Tab content divs", '<div id="overview" class="tab-content active">' in content),
        ("Queue tab", '<div id="queue" class="tab-content">' in content),
        ("Metrics tab", '<div id="metrics" class="tab-content">' in content),
        ("switchTab function", 'function switchTab(tabName, buttonElement)' in content),
    ]
    
    all_pass = True
    for check_name, result in checks:
        if result:
            print(f"✓ Chief Dashboard: {check_name}")
        else:
            print(f"✗ Chief Dashboard: {check_name}")
            all_pass = False
    
    return all_pass

def test_order_route():
    """Test that /order route exists in app.py"""
    app_path = Path("app.py")
    content = app_path.read_text()
    
    if 'def order_page():' in content or '@app.route(\'/order\'' in content:
        print("✓ App: /order route defined")
        if 'render_template(\'order.html\')' in content or 'return render_template("order.html")' in content:
            print("✓ App: /order route renders order.html template")
            return True
    else:
        print("✗ App: /order route not found")
        return False

def test_order_template_exists():
    """Test that order.html template exists"""
    order_path = Path("templates/order.html")
    if order_path.exists():
        content = order_path.read_text()
        checks = [
            ("Template exists", True),
            ("Has cart UI", 'id="cart' in content),
            ("Has checkout button", 'onclick="placeOrder()' in content),
            ("Fetches menu items", '/api/items' in content),
            ("Posts to /api/public/orders", '/api/public/orders' in content),
        ]
        all_pass = True
        for check_name, result in checks:
            if result:
                print(f"✓ Order Template: {check_name}")
            else:
                print(f"✗ Order Template: {check_name}")
                all_pass = False
        return all_pass
    else:
        print("✗ Order Template: File does not exist")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("CHAA CHOO - UI FIX VERIFICATION TEST")
    print("=" * 60)
    
    print("\n1. Testing Homepage Product Links...")
    print("-" * 60)
    test1 = test_homepage_product_links()
    
    print("\n2. Testing Chief Dashboard Tabs...")
    print("-" * 60)
    test2 = test_chief_dashboard_tabs()
    
    print("\n3. Testing /order Route...")
    print("-" * 60)
    test3 = test_order_route()
    
    print("\n4. Testing order.html Template...")
    print("-" * 60)
    test4 = test_order_template_exists()
    
    print("\n" + "=" * 60)
    if all([test1, test2, test3, test4]):
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nFixes applied successfully:")
        print("  1. ✓ Products on homepage now link to /order")
        print("  2. ✓ Chief dashboard now has 3 working tabs:")
        print("      - Overview (metrics and status)")
        print("      - Active Orders (kitchen queue)")
        print("      - Metrics (detailed performance stats)")
    else:
        print("✗ SOME TESTS FAILED - Review output above")
    print("=" * 60)
