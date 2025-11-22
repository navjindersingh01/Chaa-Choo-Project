# Dashboard Data Setup - Complete ✅

## Dummy Data Inserted

The following sample data has been automatically inserted into the database to demonstrate the dashboard functionality:

### Orders & Revenue Data
- **76 Orders** created across the last 14 days
- **187 Order Items** across all orders
- **Date Range**: Oct 31, 2025 - Nov 13, 2025
- **Business Hours**: Orders distributed between 8 AM and 6 PM daily
- **Random Items**: Each order contains 1-4 random menu items
- **Realistic Pricing**: Total amounts calculated based on actual menu prices

### Sample Revenue by Day
```
Oct 31: ₹2,260
Nov 01: ₹3,210
Nov 02: ₹2,090
Nov 03: ₹1,240
Nov 04: ₹3,490
Nov 05: ₹3,710
Nov 06: ₹2,330
Nov 07: ₹1,880
Nov 08: ₹2,750
Nov 09: ₹730
Nov 10: ₹2,770
Nov 11: ₹2,940
Nov 12: ₹3,480
Nov 13: ₹0 (Today - no orders yet)
```

### Top Selling Items
1. **Espresso** - 10 units sold
2. **Latte** - 10 units sold
3. **Sandwich** - 9 units sold
4. **Brownie** - 9 units sold
5. **Cappuccino** - 9 units sold

### Cashiers Processing Orders
- alice (chief)
- bob (receptionist)
- newchief (chief - newly created)

## Dashboard Visualization

### Manager Dashboard Features
✅ **Today's Revenue** - Shows current day revenue (₹0 if no orders today)
✅ **Revenue Trend Chart** - 14-day line chart showing daily revenue patterns
✅ **Top Selling Items Chart** - Bar chart displaying best-selling items

### Data Endpoints (Working)
- `GET /api/kpi/revenue_range?days=14` - Revenue analytics data
- `GET /api/top-items?limit=5` - Top selling items
- `GET /api/items` - All menu items

## Testing the Dashboard

### 1. Login as Manager
```bash
Username: diana
Password: 11111111
```

### 2. View Live Dashboard
Go to: `http://localhost:8081/dashboard/manager`

You will see:
- Daily revenue totals in KPI card
- Revenue trend line chart (14 days)
- Top selling items bar chart

### 3. Create More Data
If you want to add more orders, run the script again:
```bash
./venv/bin/python insert_dummy_orders.py
```

## Dashboard Roles & Access

| Role | Dashboard | Features |
|------|-----------|----------|
| Chief (alice) | `/dashboard/chief` | Order & revenue tracking |
| Receptionist (bob) | `/dashboard/receptionist` | Order creation & management |
| Inventory (charlie) | `/dashboard/inventory` | Stock level management |
| Manager (diana, eve) | `/dashboard/manager` | Full analytics + user creation |

## Database Tables with Data

### users (5 users)
- alice (chief)
- bob (receptionist)
- charlie (inventory)
- diana (manager)
- eve (manager)

### items (12 items)
- 5 Coffee items
- 2 Tea items
- 3 Pastry items
- 2 Sandwich items

### orders (76 orders)
- Distributed across 14 days
- Statuses: completed

### order_items (187 items)
- Links orders to menu items with quantities and prices

### inventory (12 entries)
- Stock levels for all menu items
- Reorder levels configured

## Next Steps

1. **Test the Manager Dashboard**: Login and view the analytics charts
2. **Create More Users**: Use the "Create New User" button on manager dashboard
3. **Place More Orders**: Via receptionist dashboard (if receptionist order creation UI is added)
4. **Monitor Analytics**: Check how charts update with new data

## Notes

- All timestamps are realistic with proper time distribution
- Quantities are random (1-3 items per order item)
- Revenue calculations are accurate based on menu prices
- Data is persistent in MySQL database
- Charts update automatically when new orders are added

---

**Dashboard Ready for Demonstration! 🎉**
