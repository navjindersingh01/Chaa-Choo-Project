# ☕ Chaa Choo - Café Management & Ordering System

A full-stack web application for managing a café's orders, inventory, and staff operations with real-time dashboards and role-based access control.

## 🌟 Features

### For Customers
- 🛒 Browse menu and place orders online
- 💬 Add special instructions/notes
- 🔄 Order type selection (Dine-in, Takeaway, Delivery)
- ✅ Real-time order status updates

### For Staff
- 📱 **Receptionist Dashboard**: Manage customer orders and inquiries
- 👨‍🍳 **Chef Dashboard**: View active orders with priority management
- 📦 **Inventory Manager**: Track stock and supplies
- 👔 **Manager Dashboard**: Oversee operations and staff
- 💼 **Stakeholder Dashboard**: View business analytics and metrics

### Admin Features
- 👥 User management and role assignment
- 🔐 Secure authentication and authorization
- 📊 Advanced analytics and reporting
- 📝 Order history and tracking
- 🎯 KPI monitoring

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask with Flask-SocketIO
- **Language**: Python 3.11+
- **Database**: MySQL 8.0
- **Server**: Gunicorn (production), Flask dev server (development)
- **Real-time**: WebSocket via Socket.IO

### Frontend
- **HTML/CSS/JavaScript**: Vanilla (No framework)
- **UI Framework**: Tailwind CSS (configured)
- **Charts**: Chart.js for analytics
- **Real-time Updates**: Socket.IO client

### Deployment
- **Reverse Proxy**: Nginx
- **Process Manager**: Systemd
- **SSL/HTTPS**: Let's Encrypt with Certbot
- **Container**: Docker & Docker Compose (optional)

## 📋 Requirements

### Development
- Python 3.11 or higher
- MySQL Server 8.0+
- Node.js (for Tailwind CSS, optional)

### Production
- Ubuntu 22.04 LTS (or similar Linux distribution)
- 2GB+ RAM minimum
- 10GB+ Storage
- Static IP address or domain

## 🚀 Quick Start (Development)

### 1. Clone or Download Project

```bash
cd ~/projects
git clone <your-repo-url> chaa-choo
cd chaa-choo
```

### 2. Setup Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

```bash
# Create MySQL database
mysql -u root -p < setup_db.sql

# Or run the setup script
python setup_db.py
```

### 5. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your database credentials
nano .env
```

### 6. Run the Application

```bash
python app.py
```

Visit `http://localhost:8080` in your browser.

## 🔐 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Chef | alice | password |
| Receptionist | bob | password |
| Manager | charlie | password |
| Inventory | diana | password |
| Stakeholder | emma | password |

**⚠️ Change these credentials immediately in production!**

## 📦 Project Structure

```
chaa-choo/
├── app.py                          # Main Flask application
├── wsgi.py                         # WSGI entry point for production
├── requirements.txt                # Python dependencies
├── .env.example                    # Example environment variables
├── .env.production                 # Production environment (don't commit)
│
├── config.py                       # Configuration management
├── gunicorn_config.py             # Gunicorn production configuration
│
├── templates/                      # HTML templates
│   ├── index.html                 # Homepage/menu
│   ├── login.html                 # Login page
│   ├── order.html                 # Order placement
│   ├── 404.html                   # Error page
│   └── dashboards/                # Role-based dashboards
│       ├── base.html              # Base dashboard layout
│       ├── chief.html             # Chef/Cook dashboard
│       ├── receptionist.html       # Receptionist dashboard
│       ├── manager.html           # Manager dashboard
│       ├── inventory.html         # Inventory manager dashboard
│       └── stakeholder.html       # Business stakeholder dashboard
│
├── static/                         # Static files
│   ├── css/
│   │   ├── style.css              # Main styles
│   │   └── dashboard.css          # Dashboard styles
│   ├── js/
│   │   └── dashboard-client.js    # Client-side dashboard logic
│   └── images/
│
├── migrations/                     # Database migrations
│   ├── upgrade_schema.py
│   ├── add_customer_fields.py
│   ├── fix_order_items_price.py
│   └── fix_order_status.py
│
├── scripts/                        # Utility scripts
│   └── run_migrations.sh
│
├── models/                         # Data models (placeholder)
├── data/                          # Data storage (placeholder)
│
├── nginx.conf                      # Nginx configuration for production
├── chaa-choo.service              # Systemd service file
├── Dockerfile                      # Docker container definition
├── docker-compose.yml             # Docker Compose orchestration
│
├── DEPLOYMENT_GUIDE.md            # Detailed deployment instructions
├── DOCKER_GUIDE.md                # Docker deployment guide
├── QUICKSTART.md                  # Quick start guide
├── RUN.md                         # Running instructions
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cafe_ca3

# Flask
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DEBUG=True

# Server
PORT=8080
HOST=0.0.0.0
```

For production, copy `.env.production` template and update values.

## 🎨 Theme & Design Tokens

This project now includes a minimal design token system and theme support.

- Tokens: `themeTokens.json` (colors, fonts, radii)
- Tailwind mapping: `tailwind.config.cjs` maps Tailwind colors to CSS variables
- CSS variables: `static/css/theme.css` contains `:root` and `[data-theme="dark"]` overrides

Preview locally:

```bash
# rebuild assets if using Tailwind/PostCSS (project may not have this step)
npm install
npm run dev
```

Toggle theme (runtime): the React `ThemeProvider` is available at `src/components/ThemeProvider.jsx`. It sets `data-theme` on the document root and persists selection to `localStorage` under `chaa-choo-theme`.

Migration guidance:

- Search/Replace hardcoded Tailwind color classes:
	- `grep -R "bg-\|text-" templates static src | grep -v "var(--"`
	- Replace with `bg-[var(--color-primary)]` or CSS tokens in `theme.css`.
- Phased rollout: add tokens, convert shared components (Header, Button, Card), convert pages.

Accessibility checks: run Lighthouse and axe DevTools; ensure focus outlines and contrast.


## 🗄️ Database Schema

### Main Tables

- **users**: Authentication and user profiles
- **orders**: Customer orders
- **order_items**: Items in each order
- **menu_items**: Available menu items
- **inventory**: Stock tracking
- **roles**: User role definitions

## 🌐 Deployment Options

### Option 1: Traditional VPS (Recommended for Hostinger)
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

```bash
# Quick deployment
bash deploy.sh
```

### Option 2: Docker (Advanced, Recommended for Scalability)
See [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

```bash
docker-compose up -d
```

### Option 3: Hostinger Website Builder (Simple)
Coming soon...

## 🔐 Security Considerations

### Development
- ✅ DEBUG mode enabled for troubleshooting
- ✅ Default credentials for testing
- ✅ CORS enabled for local development

### Production Checklist
- ❌ DEBUG=False (disable debug mode)
- ❌ Change all default passwords
- ❌ Use strong SECRET_KEY (minimum 32 characters)
- ❌ Enable HTTPS/SSL
- ❌ Setup firewall (UFW)
- ❌ Regular database backups
- ❌ Monitor logs and access
- ❌ Keep software updated
- ❌ Use environment variables for secrets

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Homepage with menu
- `GET /order` - Order placement page
- `GET /api/public/items` - Get menu items
- `POST /api/orders` - Create new order
- `GET /api/orders` - Get all orders

### Authenticated Endpoints (Dashboard)
- `GET /dashboard/<role>` - Role-specific dashboard
- `GET /api/kpi/revenue_range` - Revenue analytics
- `GET /api/top-items` - Best-selling items
- `PUT /api/orders/<id>/status` - Update order status

### Admin Endpoints
- `POST /create-user` - Create new user
- `GET /create-user` - User creation form

## 🐛 Troubleshooting

### Application Won't Start
```bash
# Check Python version
python3 --version

# Check MySQL connection
mysql -u root -p -h localhost

# View error logs
tail -f error.log
```

### Database Connection Error
```bash
# Verify credentials in .env
# Check MySQL is running
systemctl status mysql

# Test connection
mysql -u <user> -p -h localhost
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8080

# Kill the process
kill -9 <PID>
```

## 📈 Performance Tips

1. **Enable Caching**: Use Redis for session storage
2. **Database Optimization**: Index frequently queried columns
3. **Compress Assets**: Enable gzip in Nginx
4. **CDN**: Use Cloudflare for static files
5. **Monitoring**: Setup uptime monitoring and alerts

## 🤝 Contributing

Contributions welcome! Please:
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit pull request with description

## 🔎 How to preview edits locally

1. Install frontend deps and run dev server (if this repo has a separate React app):

```bash
# from repo root
npm install
npm run dev
```

2. If the React components are imported into the existing app, start the Flask dev server:

```bash
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

3. Open the app in the browser and visit the dashboard routes (e.g., `/dashboard/chef`, `/dashboard/reception`, `/dashboard/inventory`, `/dashboard/manager`, `/dashboard/finance`).

Note: The edited components use embedded mock data. Action buttons log the simulated API payload to the console so you can verify optimistic updates without a backend.

## 🔁 How to replace mock data with real APIs

1. Identify the component's TODO comment that points to the API path (e.g., `// TODO: replace with fetch('/api/chef/waste?limit=10')`).
2. Replace the mock import or default prop with a data fetching hook (SWR/react-query/axios). Example with axios:

```js
// axios usage example
import axios from 'axios'
const res = await axios.get('/api/chef/waste?limit=10', { headers: { Authorization: 'Bearer <TOKEN>' } })
const data = res.data
// Use SWR key: ['chef','waste'] and revalidateInterval: 60000
```

3. Ensure you include auth headers (JWT or session cookie) as required by your backend.
4. Replace optimistic console.log calls with real POST/PATCH requests and update local cache (SWR mutate or react-query invalidate) for optimistic UI.

## 🧭 Git workflow & PR checklist (example)

Branch naming:
```
git checkout -b edit/dashboards/<short-desc>
```

Commit message template:
```
feat(dashboards): update KPIs, mock data, refresh cadences, and actionable items
```

PR checklist (include in PR description):
- [ ] Updated `dashboard-specs.json` with `spec_version` incremented
- [ ] Updated mock data in the five dashboard components
- [ ] Added API placeholders and sample payloads for actions
- [ ] Verified KPI calculations against mock data
- [ ] Verified actionable buttons log payloads (simulate network)
- [ ] Ran `npm run dev` and confirmed dashboards render
- [ ] Added small validation helpers where applicable

## 📝 License

MIT License - Feel free to use this project commercially.

## 📞 Support

For issues and support:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review error logs: `error.log`
- Check MySQL logs for database issues
- Verify Nginx configuration: `sudo nginx -t`

## 🎯 Roadmap

- [ ] Mobile app version
- [ ] Payment gateway integration
- [ ] SMS notifications
- [ ] Email receipts
- [ ] Advanced reporting
- [ ] Kitchen display system (KDS)
- [ ] Loyalty program
- [ ] Multi-location support

## 👥 Team

- Backend: Flask + MySQL
- Frontend: HTML/CSS/JS + Tailwind
- Deployment: Nginx + Gunicorn + Docker

---

**Ready to deploy?** Start with the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Prefer Docker?** Check the [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

**Need help?** See [RUN.md](RUN.md) for detailed instructions.
