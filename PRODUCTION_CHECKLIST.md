# Chaa Choo Café - Production Deployment Checklist

**Project Name:** Chaa Choo Café  
**Deployment Date:** November 20, 2025  
**Target:** WebDedis VPS + GoDaddy Domain  
**Status:** ✅ Ready to Deploy

---

## Pre-Deployment Verification

### Code & Files
- [x] Python syntax validated (no errors in app.py)
- [x] All imports available in requirements.txt
- [x] Unused test files identified for cleanup
- [x] Configuration files ready (.env.example, gunicorn_config.py, nginx.conf)
- [x] WSGI entry point configured (wsgi.py)
- [x] Static files organized
- [x] Database schema prepared

### Dependencies
- [x] Flask >= 3.0.0
- [x] mysql-connector-python >= 8.0.33
- [x] flask-socketio >= 5.3.0
- [x] gunicorn >= 21.0.0
- [x] python-dotenv >= 1.0.0
- [x] All other dependencies pinned to specific versions

### Features
- [x] Public order page (`/order`) - fully functional
- [x] Manager dashboard (`/dashboard/manager`) - all features working
- [x] Menu management API + UI (add/edit/delete with image upload)
- [x] User management API + UI (add/delete staff)
- [x] Order export (CSV/JSON) + clear orders
- [x] Recent orders list display
- [x] KPI charts and analytics
- [x] Health check endpoint (`/health`)

### Security
- [x] Role-based access control (receptionist, chief, inventory, manager)
- [x] Password hashing (Werkzeug)
- [x] Manager endpoints protected with @role_required
- [x] No hardcoded secrets in codebase
- [x] .env.example provides template (not committed)
- [x] CSRF protection ready (Flask default)

### Database
- [x] Schema supports: users, items, orders, order_items, inventory, order_history
- [x] Sample menu data in `data/menu.json`
- [x] Setup script ready (`setup_db.py`)
- [x] Default manager account prepared

### Documentation
- [x] DEPLOY_FINAL.md (comprehensive guide)
- [x] PRODUCTION_CHECKLIST.md (this file)
- [x] README.md (project overview)
- [x] .env.example (environment template)

---

## VPS Setup Tasks

### Pre-Installation
- [ ] Obtain VPS IP from WebDedis
- [ ] Verify SSH access: `ssh root@<VPS_IP>`
- [ ] Verify OS (Ubuntu 22.04 LTS recommended)

### System Packages
- [ ] Update packages: `apt-get update && apt-get upgrade -y`
- [ ] Install Python 3.11: `apt-get install python3.11 python3.11-venv`
- [ ] Install MySQL Server: `apt-get install mysql-server`
- [ ] Install Nginx: `apt-get install nginx`
- [ ] Install certbot: `apt-get install certbot python3-certbot-nginx`
- [ ] Install git: `apt-get install git`

### User & Directory Setup
- [ ] Create `chaa-choo` user
- [ ] Create `/home/chaa-choo/app` directory
- [ ] Create `/var/log/chaa-choo` directory
- [ ] Set proper permissions (755 for dirs, 644 for files)

### MySQL Setup
- [ ] Start MySQL service
- [ ] Create database: `chaa_choo_db`
- [ ] Create user: `chaa_choo_user` with strong password
- [ ] Grant privileges
- [ ] Test connection

---

## Domain Configuration (GoDaddy)

- [ ] Log in to GoDaddy DNS Management
- [ ] Add **A Record** pointing to VPS IP:
  - Name: `@` (root domain)
  - Type: A
  - Value: `<VPS_IP_ADDRESS>`
  - TTL: 3600
  
- [ ] Add **A Record** for www (optional):
  - Name: `www`
  - Type: A
  - Value: `<VPS_IP_ADDRESS>`
  - TTL: 3600

- [ ] Wait 24-48 hours for DNS propagation
- [ ] Verify with: `nslookup yourdomain.com`

---

## Application Deployment

### Repository Setup
- [ ] Clone repo or upload files via SFTP
- [ ] Navigate to `/home/chaa-choo/app`
- [ ] Set ownership: `chown -R chaa-choo:chaa-choo .`

### Virtual Environment
- [ ] Create venv: `python3.11 -m venv venv`
- [ ] Activate: `source venv/bin/activate`
- [ ] Upgrade pip: `pip install --upgrade pip setuptools wheel`
- [ ] Install requirements: `pip install -r requirements.txt`

### Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Edit `.env` with production values:
  - [ ] `DB_HOST=localhost`
  - [ ] `DB_USER=chaa_choo_user`
  - [ ] `DB_PASSWORD=<STRONG_PASSWORD>`
  - [ ] `DB_NAME=chaa_choo_db`
  - [ ] `SECRET_KEY=<GENERATE_NEW>`
  - [ ] `FLASK_ENV=production`
  - [ ] `DEBUG=False`

### Database Initialization
- [ ] Run setup: `python3 setup_db.py`
- [ ] Verify tables created
- [ ] Test connection from VPS

### File Permissions
- [ ] Set app ownership: `chown -R chaa-choo:chaa-choo /home/chaa-choo/app`
- [ ] Set dir permissions: `chmod 755 /home/chaa-choo/app`
- [ ] Set data permissions: `chmod 775 /home/chaa-choo/app/data`
- [ ] Set images permissions: `chmod 775 /home/chaa-choo/app/static/images/menu`
- [ ] Set log permissions: `chmod 775 /var/log/chaa-choo`

---

## SSL/TLS Certificate

- [ ] Run certbot: `sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com`
- [ ] Verify certificates at: `/etc/letsencrypt/live/yourdomain.com/`
- [ ] Update nginx.conf with domain name
- [ ] Copy nginx.conf to: `/etc/nginx/sites-available/chaa-choo`
- [ ] Create symlink: `sudo ln -s /etc/nginx/sites-available/chaa-choo /etc/nginx/sites-enabled/chaa-choo`
- [ ] Test nginx config: `sudo nginx -t`
- [ ] Reload nginx: `sudo systemctl reload nginx`
- [ ] Set up auto-renewal: `sudo certbot renew --dry-run`

---

## Systemd Service Setup

- [ ] Create service file: `/etc/systemd/system/chaa-choo.service`
- [ ] Set content with gunicorn config
- [ ] Reload systemd: `sudo systemctl daemon-reload`
- [ ] Enable service: `sudo systemctl enable chaa-choo`
- [ ] Start service: `sudo systemctl start chaa-choo`
- [ ] Verify status: `sudo systemctl status chaa-choo`

### Log Rotation
- [ ] Create `/etc/logrotate.d/chaa-choo` config
- [ ] Test rotation: `sudo logrotate -f /etc/logrotate.d/chaa-choo`

---

## Verification

### Service Status
- [ ] Flask app running: `sudo systemctl status chaa-choo`
- [ ] Nginx running: `sudo systemctl status nginx`
- [ ] MySQL running: `sudo systemctl status mysql`

### Network Tests
- [ ] HTTP redirect to HTTPS: `curl -I http://yourdomain.com`
- [ ] HTTPS response: `curl -I https://yourdomain.com`
- [ ] Health check: `curl https://yourdomain.com/health`
- [ ] Logs show no errors

### Application Tests
- [ ] Public page loads: `https://yourdomain.com`
- [ ] Order page works: `https://yourdomain.com/order`
- [ ] Login works: `https://yourdomain.com/login`
- [ ] Manager dashboard loads: `https://yourdomain.com/dashboard/manager`

---

## Post-Deployment

### Security Hardening
- [ ] Change default `diana` password immediately
- [ ] Delete `diana` user after creating new admin
- [ ] Enable firewall (ufw)
- [ ] Configure fail2ban (optional)
- [ ] Review nginx security headers

### Monitoring Setup
- [ ] Set up backup script
- [ ] Configure cron for daily backups
- [ ] Test email alerts
- [ ] Monitor disk space
- [ ] Monitor memory usage

### Documentation
- [ ] Document database credentials (secure location)
- [ ] Document admin account credentials
- [ ] Document SSH key access
- [ ] Create runbook for common tasks

---

## Cleanup Tasks

### Files to Remove from Production
- [ ] `test_end_to_end.py` (test file)
- [ ] `test_fixes.py` (test file)
- [ ] `insert_dummy_orders.py` (test data)
- [ ] `set_passwords_and_roles.py` (setup script)
- [ ] `update_alice_password.py` (legacy script)
- [ ] `CHANGELOG.md` (development log)
- [ ] `CHANGES_DETAILED.md` (development log)
- [ ] `DEPLOYMENT_COMPLETE.md` (old guide)
- [ ] `DEPLOYMENT_GUIDE.md` (old guide)
- [ ] `DEPLOYMENT_READY.md` (old guide)
- [ ] `DOCKER_GUIDE.md` (unused)
- [ ] `Dockerfile` (if not using containers)
- [ ] `docker-compose.yml` (if not using containers)
- [ ] `.vscode/` (VSCode settings - keep locally only)
- [ ] `error.log` (old logs)
- [ ] `ISSUES_RESOLVED.txt` (development notes)
- [ ] `FIXES_SUMMARY.md` (development notes)
- [ ] `FIXES_VERIFICATION.md` (development notes)
- [ ] `IMPLEMENTATION.md` (development notes)
- [ ] `SOLUTION_SUMMARY.md` (development notes)
- [ ] `.env` (never commit - generate on VPS)

### Files to Keep
- [x] `app.py` (main application)
- [x] `wsgi.py` (WSGI entry point)
- [x] `gunicorn_config.py` (production config)
- [x] `requirements.txt` (dependencies)
- [x] `.env.example` (template)
- [x] `nginx.conf` (web server config)
- [x] `chaa-choo.service` (systemd service)
- [x] `data/menu.json` (menu data)
- [x] `static/` (CSS, JS, images)
- [x] `templates/` (HTML templates)
- [x] `setup_db.py` (for initial setup)
- [x] `scripts/` (utility scripts)
- [x] `migrations/` (database migrations)
- [x] `README.md` (project info)
- [x] `DEPLOY_FINAL.md` (deployment guide)
- [x] `PRODUCTION_CHECKLIST.md` (this file)

---

## Rollback Procedure

If issues arise after deployment:

```bash
# 1. Stop the service
sudo systemctl stop chaa-choo

# 2. Restore from backup (if available)
cd /home/chaa-choo/app
git reset --hard HEAD~1  # Or restore from backup

# 3. Restart service
sudo systemctl start chaa-choo

# 4. Check logs
journalctl -u chaa-choo -n 100
```

---

## Contact & Support

**For VPS Issues:** Contact WebDedis support  
**For Domain Issues:** Contact GoDaddy support  
**For Application Issues:** Check `/var/log/chaa-choo/error.log`

---

## Sign-Off

- **Deployment Date:** ______________
- **Deployed By:** ______________
- **Verified By:** ______________
- **Notes:** ______________

---

**Last Updated:** November 20, 2025  
**Status:** ✅ Ready for Production
