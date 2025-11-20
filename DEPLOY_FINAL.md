# Chaa Choo Café - Production Deployment Guide
## WebDedis VPS + GoDaddy Domain

**Last Updated:** November 20, 2025  
**Status:** Production-Ready

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [VPS Setup (WebDedis)](#vps-setup-webdedis)
3. [Domain Configuration (GoDaddy)](#domain-configuration-godaddy)
4. [Application Deployment](#application-deployment)
5. [Database Setup](#database-setup)
6. [SSL/TLS Certificate](#ssltls-certificate)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

- [x] All Python files validated (no syntax errors)
- [x] Requirements.txt updated with specific versions
- [x] .env.example template created
- [x] Gunicorn config ready
- [x] Nginx config ready
- [x] Manager dashboard features (Menu, Users, Orders) functional
- [x] Database schema validated
- [x] Static files organized
- [x] Unused files cleaned up

---

## VPS Setup (WebDedis)

### Step 1: SSH into VPS
```bash
ssh root@your-vps-ip-address
```

### Step 2: Update System Packages
```bash
apt-get update
apt-get upgrade -y
```

### Step 3: Install Required Packages
```bash
apt-get install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  mysql-server \
  nginx \
  git \
  certbot \
  python3-certbot-nginx \
  supervisor \
  curl \
  wget \
  build-essential \
  libmysqlclient-dev
```

### Step 4: Create Application User
```bash
# Create dedicated user for the app
useradd -m -s /bin/bash chaa-choo

# Create application directory
mkdir -p /home/chaa-choo/app
chown -R chaa-choo:chaa-choo /home/chaa-choo/app

# Create log directory
mkdir -p /var/log/chaa-choo
chown -R chaa-choo:chaa-choo /var/log/chaa-choo
```

### Step 5: MySQL Setup
```bash
# Start MySQL and create database
sudo mysql -u root

# Inside MySQL:
CREATE DATABASE chaa_choo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'chaa_choo_user'@'localhost' IDENTIFIED BY 'YOUR_STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON chaa_choo_db.* TO 'chaa_choo_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## Domain Configuration (GoDaddy)

### Step 1: Point Domain to VPS
1. **Log in to GoDaddy** → **DNS Management**
2. **Find Nameservers or DNS Records** section
3. Update the **A Record** to point to your VPS IP:
   - **Name:** `@` (or leave blank for root domain)
   - **Type:** A
   - **Value:** Your VPS IP address (e.g., `123.45.67.89`)
   - **TTL:** 3600

4. Add **WWW subdomain** (optional):
   - **Name:** `www`
   - **Type:** A
   - **Value:** Your VPS IP address
   - **TTL:** 3600

**DNS Propagation Time:** 24-48 hours (usually faster)

### Verify Domain Resolution
```bash
# From your VPS (after DNS propagates):
nslookup yourdomain.com
dig yourdomain.com
```

---

## Application Deployment

### Step 1: Clone Repository
```bash
cd /home/chaa-choo/app
git clone https://github.com/yourusername/chaa-choo.git .
chown -R chaa-choo:chaa-choo /home/chaa-choo/app
```

**Or** upload files via SFTP/SCP if no git repo.

### Step 2: Create Python Virtual Environment
```bash
cd /home/chaa-choo/app
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit with your production values
nano .env
```

**Critical values to set:**
- `DB_HOST=localhost`
- `DB_USER=chaa_choo_user`
- `DB_PASSWORD=YOUR_STRONG_PASSWORD`
- `DB_NAME=chaa_choo_db`
- `SECRET_KEY=<generate new with: python3 -c "import secrets; print(secrets.token_hex(32))">
- `FLASK_ENV=production`
- `DEBUG=False`
- `LOG_FILE=/var/log/chaa-choo/app.log`

### Step 4: Initialize Database
```bash
source venv/bin/activate
python3 setup_db.py
```

This will:
- Create tables (users, items, orders, order_items, inventory)
- Insert sample menu from `data/menu.json`
- Create default manager user `diana` (password: `password`)

### Step 5: Fix File Permissions
```bash
cd /home/chaa-choo/app
chown -R chaa-choo:chaa-choo .
chmod -R 755 .
chmod -R 775 data/ static/images/menu/ /var/log/chaa-choo/
```

---

## SSL/TLS Certificate

### Step 1: Obtain Let's Encrypt Certificate
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

When prompted:
- Enter your email address
- Agree to terms
- Enter your domain(s)

Certificates stored at: `/etc/letsencrypt/live/yourdomain.com/`

### Step 2: Update Nginx Config
```bash
# Copy provided nginx.conf to your VPS
sudo cp /home/chaa-choo/app/nginx.conf /etc/nginx/sites-available/chaa-choo

# Edit to set your domain
sudo nano /etc/nginx/sites-available/chaa-choo
```

Replace `yourdomain.com` with your actual domain (appears 4 times).

### Step 3: Enable Nginx Site
```bash
sudo ln -s /etc/nginx/sites-available/chaa-choo /etc/nginx/sites-enabled/chaa-choo

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

### Step 4: Auto-Renew Certificate
```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Enable auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Application Deployment

### Step 1: Create Systemd Service
```bash
sudo nano /etc/systemd/system/chaa-choo.service
```

Paste:
```ini
[Unit]
Description=Chaa Choo Café Flask Application
After=network.target mysql.service

[Service]
Type=notify
User=chaa-choo
Group=chaa-choo
WorkingDirectory=/home/chaa-choo/app
Environment="PATH=/home/chaa-choo/app/venv/bin"
ExecStart=/home/chaa-choo/app/venv/bin/gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 127.0.0.1:5000 \
  --timeout 60 \
  --access-logfile /var/log/chaa-choo/access.log \
  --error-logfile /var/log/chaa-choo/error.log \
  --log-level info \
  wsgi:app

Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save (Ctrl+O, Enter, Ctrl+X).

### Step 2: Enable & Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable chaa-choo
sudo systemctl start chaa-choo

# Verify
sudo systemctl status chaa-choo
```

### Step 3: Create Gunicorn Log Rotation
```bash
sudo nano /etc/logrotate.d/chaa-choo
```

Paste:
```
/var/log/chaa-choo/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 chaa-choo chaa-choo
    sharedscripts
    postrotate
        systemctl reload chaa-choo > /dev/null 2>&1 || true
    endscript
}
```

---

## Verification

### Check Services Status
```bash
# Flask app
sudo systemctl status chaa-choo

# Nginx
sudo systemctl status nginx

# MySQL
sudo systemctl status mysql
```

### Test URLs
```bash
# Public page
curl http://yourdomain.com

# HTTPS (after SSL setup)
curl https://yourdomain.com

# API health check
curl https://yourdomain.com/health
```

### View Logs
```bash
# Application logs
tail -f /var/log/chaa-choo/error.log
tail -f /var/log/chaa-choo/access.log

# Nginx logs
tail -f /var/log/nginx/chaa-choo-error.log

# Systemd logs
journalctl -u chaa-choo -f
```

---

## Monitoring & Maintenance

### Database Backups
```bash
#!/bin/bash
# Save as: /home/chaa-choo/backup-db.sh

BACKUP_DIR="/home/chaa-choo/backups"
DATE=$(date +\%Y\%m\%d_\%H\%M\%S)
DB_NAME="chaa_choo_db"
DB_USER="chaa_choo_user"

mkdir -p $BACKUP_DIR
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

Schedule with cron:
```bash
crontab -e
# Add: 0 2 * * * /home/chaa-choo/backup-db.sh
```

### Check Application Health
```bash
# Every 5 minutes
curl -s https://yourdomain.com/health | grep -q "healthy" && echo "OK" || echo "DOWN"
```

### Monitor Resource Usage
```bash
# Memory
free -h

# Disk
df -h

# Process
ps aux | grep gunicorn
```

---

## Troubleshooting

### Application won't start
```bash
# Check syntax
sudo systemctl start chaa-choo
sudo journalctl -u chaa-choo -n 50 -e

# Check Python
source venv/bin/activate
python3 -c "from app import app; print('OK')"
```

### Database connection error
```bash
# Test MySQL
mysql -u chaa_choo_user -p -h localhost -e "SELECT 1"

# Check .env
grep DB_ /home/chaa-choo/app/.env

# Verify DB exists
mysql -u chaa_choo_user -p -e "SHOW DATABASES;"
```

### Nginx 502 Bad Gateway
```bash
# Ensure app is running
sudo systemctl status chaa-choo

# Check socket
netstat -tlnp | grep 5000

# Check Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Domain not resolving
```bash
# Check DNS
nslookup yourdomain.com
dig yourdomain.com

# Wait 24-48 hours for propagation
# Check with: https://www.whatsmydns.net/
```

### SSL certificate issues
```bash
# Check cert
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Check logs
sudo systemctl status certbot.timer
```

---

## Post-Deployment

1. **Change Default Credentials**
   - Log in as `diana` / `password`
   - Create new manager account with strong password
   - Delete `diana` user from Manager Dashboard

2. **Test All Features**
   - Place test order on `/order`
   - Access `/dashboard/manager`
   - Test menu management
   - Test user management
   - Test order export

3. **Set Up Monitoring**
   - Configure email alerts for systemd
   - Set up log rotation
   - Schedule database backups

4. **Secure the VPS**
   ```bash
   # Firewall (ufw)
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

---

## Support & Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **Gunicorn Documentation:** https://gunicorn.org/
- **Nginx Documentation:** https://nginx.org/
- **Let's Encrypt:** https://letsencrypt.org/
- **WebDedis Support:** Contact your provider

---

**Deployment completed on:** November 20, 2025

For any issues, check logs first:
```bash
tail -f /var/log/chaa-choo/error.log
journalctl -u chaa-choo -f
```
