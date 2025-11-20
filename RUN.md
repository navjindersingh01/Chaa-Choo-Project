# Chaa Choo Café - Quick Start Guide

## Prerequisites
- MySQL running locally on port 3306
- Python 3.14+ with venv (created at `./venv`)

## Important: Environment Variables

All database credentials and configuration are now managed via **environment variables only**. No hardcoded credentials are stored in the codebase.

### Set Environment Variables Before Running

Copy `.env.example` to `.env` and set your values:
```bash
cp .env.example .env
```

Then set them in your terminal:
```bash
export DB_HOST=127.0.0.1
export DB_USER=root
export DB_PASSWORD=11111111
export DB_NAME=cafe_ca3
export SECRET_KEY=your_secret_key_here
```

Or pass them directly when starting the app:
```bash
DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=11111111 DB_NAME=cafe_ca3 PORT=8081 nohup ./venv/bin/python app.py > /tmp/flask_run.log 2>&1 &
```

## Start the App

### Step 1: Navigate to the project directory
```bash
cd "/Users/dhaliwal/Documents/Lovely professional University/LPU CA's/CA's/Smester 5/MGN343 (Business Intelligence)/CA2/VS code/Chaa Choo"
```

### Step 2: Set environment variables (one-time)
```bash
export DB_HOST=127.0.0.1
export DB_USER=root
export DB_PASSWORD=11111111
export DB_NAME=cafe_ca3
```

### Step 3: Stop any existing process on port 8081 (if any)
```bash
lsof -ti tcp:8081 | xargs -r kill -9
sleep 1
```

### Step 4: Start the Flask app
```bash
PORT=8081 nohup ./venv/bin/python app.py > /tmp/flask_run.log 2>&1 &
```

This will:
- Start the app on **http://localhost:8081/**
- Run it in the background (nohup)
- Log output to `/tmp/flask_run.log`

### Step 5: Verify the app is running
```bash
curl -I http://127.0.0.1:8081/
```

Expected output:
```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.14.0
...
```

## Login Credentials

All users use password: **`11111111`**

| Username | Role | Purpose | Can Create Users? |
|----------|------|---------|-------------------|
| alice | chief | Cook — prepares orders | ❌ |
| bob | receptionist | Takes customer orders at desk | ❌ |
| charlie | inventory | Manages stock levels | ❌ |
| diana | manager | Business analytics & user creation | ✅ |
| eve | manager | Business analytics & user creation | ✅ |

## Manager Features

**Only managers (diana, eve) can:**
1. Access the manager dashboard at `/dashboard/manager`
2. Create new users via `/manager/create_user`
3. Assign roles to new users: **chief**, **receptionist**, **inventory**, or **manager**

### How to Create a New User (as Manager)

1. Login as `diana` or `eve` with password `11111111`
2. Go to `/manager/create_user`
3. Fill in:
   - **Username**: lowercase (e.g., `newchief`)
   - **Password**: any password you want
   - **Role**: choose from chief, receptionist, inventory, or manager
4. Click "Create User"
5. New user can immediately login with their credentials

## Common Commands

### View live logs
```bash
tail -f /tmp/flask_run.log
```

### Stop the app
```bash
lsof -ti tcp:8081 | xargs -r kill -9
```

### Test a login (example: bob)
```bash
curl -i -X POST -d "username=bob&password=11111111" http://localhost:8081/login
```

Expected: HTTP 302 redirect to `/dashboard/receptionist`

### Open in browser
Go to: **http://localhost:8081/**

## Features

- **Home page**: Browse menu items with prices (public access, no login required)
- **Login**: Authentication with username & password
- **Dashboards**: Role-specific dashboards with analytics
  - **Chief (Cook)**: Order & revenue tracking
  - **Receptionist**: Order creation & management
  - **Inventory**: Stock level management & reorder alerts
  - **Manager**: Business analytics, revenue reports, and create new users
- **Manager Only**: Create new users at `/manager/create_user`

## Database

The database `cafe_ca3` is created automatically on first setup with sample data:
- 5 initial users (alice, bob, charlie, diana, eve)
- 12 menu items (coffees, teas, pastries, sandwiches)
- Inventory data for all items

### Reset Database

If you need to reset and reinitialize the database:
```bash
./venv/bin/python setup_db.py
```

This will:
1. Drop and recreate all tables
2. Insert initial users and menu items
3. Set up inventory levels

## Troubleshooting

**Port already in use:**
```bash
lsof -i :8081
kill -9 <PID>
```

**Check app errors:**
```bash
tail -n 200 /tmp/flask_run.log
```

**MySQL connection issues:**
Make sure MySQL is running:
```bash
brew services start mysql
```

**Environment variables not set:**
Make sure to `export` variables before starting the app:
```bash
export DB_HOST=127.0.0.1
export DB_USER=root
export DB_PASSWORD=11111111
export DB_NAME=cafe_ca3
PORT=8081 ./venv/bin/python app.py
```

## Security Notes

- ✅ **No hardcoded credentials** in the codebase
- ✅ **Environment variables only** for sensitive data
- ✅ **Password hashing** with Werkzeug (bcrypt-based)
- ✅ **Session management** with Flask secure cookies
- ❌ `/dev/create_user` endpoint is disabled in production (only for initial dev setup)

See `.gitignore` for files excluded from version control (config.py, .env, logs, etc.)
