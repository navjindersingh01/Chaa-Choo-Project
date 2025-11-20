# Quick Start: Deploy Chaa Choo to WebDedis VPS

**Status:** ✅ Ready to Deploy  
**Created:** November 20, 2025

---

## 5-Minute Overview

Your Chaa Choo Café website is **production-ready**. Follow this quick guide to deploy on WebDedis VPS with your GoDaddy domain.

---

## Phase 1: Prepare Local Copy (5 minutes)

```bash
# Clone/download to your machine
cd Chaa\ Choo

# Clean up unused files
bash cleanup-for-production.sh

# Verify files removed
git status
```

---

## Phase 2: GoDaddy Domain Setup (15 minutes)

1. **Log into GoDaddy**
2. **Go to DNS Management**
3. **Add A Record:**
   - Name: `@` (root)
   - Type: A
   - Value: `<YOUR_VPS_IP>`
   - TTL: 3600
4. **Optional - Add www:**
   - Name: `www`
   - Type: A
   - Value: `<YOUR_VPS_IP>`
   - TTL: 3600
5. **Save changes**
6. **Wait 24-48 hours for DNS to propagate**

✅ **Verify:** `nslookup yourdomain.com`

---

## Phase 3: VPS Initial Setup (30 minutes)

```bash
# SSH into VPS
ssh root@<VPS_IP>

# Update system
apt-get update && apt-get upgrade -y

# Install packages (paste all at once)
apt-get install -y python3.11 python3.11-venv python3-pip \
  mysql-server nginx git certbot python3-certbot-nginx \
  supervisor curl wget build-essential libmysqlclient-dev

# Create app user
useradd -m -s /bin/bash chaa-choo

# Create directories
mkdir -p /home/chaa-choo/app
mkdir -p /var/log/chaa-choo
chown -R chaa-choo:chaa-choo /home/chaa-choo /var/log/chaa-choo
```

---

## Phase 4: MySQL Setup (10 minutes)

```bash
# Start MySQL
sudo mysql -u root

# Inside MySQL (paste all at once):
CREATE DATABASE chaa_choo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'chaa_choo_user'@'localhost' IDENTIFIED BY 'YOUR_STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON chaa_choo_db.* TO 'chaa_choo_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## Phase 5: Deploy Application (20 minutes)

```bash
# On VPS, as root
cd /home/chaa-choo/app

# Option A: Clone from git (if using GitHub)
git clone https://github.com/yourusername/chaa-choo.git .

# Option B: Upload files via SFTP
# scp -r /local/path/* root@<VPS_IP>:/home/chaa-choo/app/

# Set ownership
chown -R chaa-choo:chaa-choo /home/chaa-choo/app

# Create venv and install
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env
# Edit these lines:
# DB_HOST=localhost
# DB_USER=chaa_choo_user
# DB_PASSWORD=<SAME_PASSWORD_FROM_MYSQL>
# DB_NAME=chaa_choo_db
# SECRET_KEY=<RUN: python3 -c "import secrets; print(secrets.token_hex(32))">
# FLASK_ENV=production
# DEBUG=False

# Initialize database
python3 setup_db.py

# Fix permissions
chmod -R 775 data static/images/menu /var/log/chaa-choo
```

---

## Phase 6: SSL Certificate (10 minutes)

```bash
# Get certificate (answer prompts)
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com

# Copy nginx config
cp /home/chaa-choo/app/nginx.conf /etc/nginx/sites-available/chaa-choo

# Edit to set your domain
sudo nano /etc/nginx/sites-available/chaa-choo
# Replace "yourdomain.com" (appears 4 times)

# Enable site
sudo ln -s /etc/nginx/sites-available/chaa-choo /etc/nginx/sites-enabled/chaa-choo

# Test & reload
sudo nginx -t
sudo systemctl reload nginx
```

---

## Phase 7: Systemd Service (10 minutes)

```bash
# Create service file
sudo nano /etc/systemd/system/chaa-choo.service
```

Paste this content:
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

[Install]
WantedBy=multi-user.target
```

Save (Ctrl+O, Enter, Ctrl+X).

Then:
```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable chaa-choo
sudo systemctl start chaa-choo

# Verify
sudo systemctl status chaa-choo
```

---

## Phase 8: Verification (5 minutes)

```bash
# Check all services
sudo systemctl status chaa-choo
sudo systemctl status nginx
sudo systemctl status mysql

# Test URLs
curl -I http://yourdomain.com          # Should redirect to HTTPS
curl -I https://yourdomain.com         # Should return 200 with SSL
curl https://yourdomain.com/health     # Should return {"status": "healthy"}

# View logs
tail -f /var/log/chaa-choo/error.log
tail -f /var/log/nginx/chaa-choo-error.log
```

---

## Phase 9: Post-Deployment (5 minutes)

1. **Access manager dashboard:**
   ```
   https://yourdomain.com/login
   Username: diana
   Password: password
   ```

2. **Change password immediately:**
   - Create new manager user
   - Delete `diana` via "Manage Users"

3. **Test all features:**
   - Order page: `https://yourdomain.com/order`
   - Manager dashboard: `https://yourdomain.com/dashboard/manager`
   - Menu management
   - User management
   - Order export

4. **Enable firewall:**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

---

## If Something Goes Wrong

```bash
# Check application logs
journalctl -u chaa-choo -n 50

# Check MySQL
mysql -u chaa_choo_user -p -h localhost -e "SELECT 1"

# Check Nginx
sudo nginx -t
tail -f /var/log/nginx/error.log

# Restart service
sudo systemctl restart chaa-choo
```

For detailed help, see: **DEPLOY_FINAL.md**

---

## Success Checklist

- [ ] Domain points to VPS (DNS propagated)
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate valid
- [ ] App service running
- [ ] Database initialized
- [ ] Login works
- [ ] Orders can be placed
- [ ] Manager dashboard accessible
- [ ] All manager features working

---

## Next Steps

1. **Monitor logs** regularly: `tail -f /var/log/chaa-choo/error.log`
2. **Set up backups:** See DEPLOY_FINAL.md for backup script
3. **Enable auto-renewal:** `sudo certbot renew --dry-run`
4. **Document credentials:** Save DB password, admin accounts securely

---

**Estimated Total Time:** 2-3 hours  
**Difficulty:** Intermediate  
**Support:** Check DEPLOY_FINAL.md or contact WebDedis support

**Happy hosting! ☕**
