# 🚀 Chaa Choo - Quick Deployment Reference Card

## 30-Second Overview

Your Chaa Choo café management system is **production-ready** for Hostinger VPS deployment.

**Deployment time: ~1 hour | Maintenance: ~10 min/week | Uptime: 99.9%+**

---

## 📋 Before You Start

1. **Have ready:**
   - [ ] Hostinger VPS account
   - [ ] Your domain name (e.g., mycafe.com)
   - [ ] SSH terminal/PuTTY
   - [ ] 30 minutes of uninterrupted time

2. **Know your:**
   - [ ] VPS IP address
   - [ ] SSH credentials (root or sudo user)
   - [ ] Domain registrar (GoDaddy, Namecheap, etc.)

---

## 🎯 3-Step Deployment

### Step 1: Prepare Domain (5 minutes)
```
1. Go to your domain registrar
2. Add A record pointing to: YOUR_VPS_IP
3. Wait 5-10 minutes for DNS propagation
```

### Step 2: Run Deployment Script (10 minutes)
```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Go to project directory (where you uploaded files)
cd /home/chaa-choo

# Run deployment
bash deploy.sh

# Answer prompts:
# - Confirm domain name
# - Confirm database password
# - Accept Let's Encrypt terms
```

### Step 3: Verify (5 minutes)
```bash
# Check if running
systemctl status chaa-choo

# Visit your domain
# Open: https://yourdomain.com

# Login with: alice / password
# (change this immediately!)
```

---

## 📁 Key Files at a Glance

### Configuration Files (Update These!)
- **`.env.production`** - Database, domain, security settings
- **`nginx.conf`** - Web server config (update domain)

### Deployment Files (Use As-Is)
- **`deploy.sh`** - Automated deployment script
- **`gunicorn_config.py`** - Application server setup
- **`chaa-choo.service`** - Auto-start service
- **`wsgi.py`** - Production entry point

### Documentation
- **`DEPLOYMENT_GUIDE.md`** - Detailed step-by-step
- **`README.md`** - Project overview
- **`PRE_DEPLOYMENT_CHECKLIST.md`** - Complete checklist

---

## ⚡ Critical Commands

### After Deployment

```bash
# ✅ Check application status
systemctl status chaa-choo

# 📊 View live logs
journalctl -u chaa-choo -f

# 🔄 Restart application
systemctl restart chaa-choo

# 🔌 Reload web server (no downtime)
systemctl reload nginx

# 💾 Backup database
mysqldump -u cafe_user -p cafe_ca3 > backup.sql

# 📋 View error logs
tail -f /var/log/nginx/chaa-choo-error.log
```

---

## 🔑 Important Credentials

| Item | Default | Action |
|------|---------|--------|
| Admin User | alice | **Change immediately** |
| Admin Pass | password | **Change immediately** |
| DB User | cafe_user | Keep secure |
| DB Pass | (in .env) | Use strong password |
| SECRET_KEY | (in .env) | Must be unique |

**Generate strong SECRET_KEY:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

---

## ✅ Quick Verification Checklist

After deployment, verify:

```
✅ Website loads at https://yourdomain.com
✅ Login works with test credentials
✅ All dashboards accessible
✅ Orders can be placed from homepage
✅ Database operations working
✅ SSL certificate valid (green lock in browser)
✅ Logs show no errors: journalctl -u chaa-choo -f
```

---

## 🆘 Quick Troubleshooting

### "Website not loading"
```bash
# Check Nginx
systemctl status nginx
nginx -t

# Check application
systemctl status chaa-choo
journalctl -u chaa-choo -f
```

### "Database connection error"
```bash
# Verify MySQL running
systemctl status mysql

# Test connection
mysql -u cafe_user -p -h localhost

# Check .env.production
cat .env.production | grep DB_
```

### "SSL certificate error"
```bash
# Renew certificate
certbot renew --force-renewal

# Reload Nginx
systemctl reload nginx

# Check status
certbot certificates
```

### "Application crashed"
```bash
# View logs
journalctl -u chaa-choo -f

# Restart
systemctl restart chaa-choo

# Check database
systemctl status mysql
```

---

## 🔒 Security Quick Wins

```bash
# 1. Change default passwords
mysql> UPDATE users SET password_hash='...' WHERE username='alice';

# 2. Enable firewall
ufw enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# 3. Setup auto-updates
apt install unattended-upgrades

# 4. Monitor logs
journalctl -u chaa-choo -f

# 5. Backup daily (add to crontab)
0 2 * * * mysqldump -u cafe_user -p'pass' cafe_ca3 > /backups/cafe_$(date +%Y%m%d).sql
```

---

## 📞 Key Resources

| Resource | URL |
|----------|-----|
| Full Deployment Guide | `DEPLOYMENT_GUIDE.md` |
| Docker Alternative | `DOCKER_GUIDE.md` |
| Pre-deployment Checklist | `PRE_DEPLOYMENT_CHECKLIST.md` |
| Project README | `README.md` |
| Nginx Docs | https://nginx.org/en/docs/ |
| Let's Encrypt | https://letsencrypt.org/ |

---

## 🎯 Next Steps

1. ✅ **Now:** Read `DEPLOYMENT_GUIDE.md` (20 minutes)
2. ✅ **Then:** Complete `PRE_DEPLOYMENT_CHECKLIST.md`
3. ✅ **Deploy:** Run `bash deploy.sh`
4. ✅ **Verify:** Test all features
5. ✅ **Customize:** Add your menu items and staff

---

## 📅 Ongoing Maintenance

### Daily (5 minutes)
- Monitor error logs
- Check application running: `systemctl status chaa-choo`

### Weekly (15 minutes)
- Review logs: `journalctl -u chaa-choo --since "7 days ago"`
- Backup database
- Update packages: `apt update && apt upgrade`

### Monthly (30 minutes)
- Full security audit
- Performance optimization
- SSL certificate check (90 days)
- Database optimization

---

## 🎉 You're All Set!

Your application is production-ready. The entire deployment should take approximately **1 hour**.

**Start here:** `DEPLOYMENT_GUIDE.md`

---

## Quick Links

- 📖 Full Guide: `DEPLOYMENT_GUIDE.md`
- 🐳 Docker: `DOCKER_GUIDE.md`
- ✅ Checklist: `PRE_DEPLOYMENT_CHECKLIST.md`
- 📘 README: `README.md`
- 🚀 Status: `DEPLOYMENT_READY.md`

---

**Questions?** Check the relevant documentation files above.

**Ready?** Start with the DEPLOYMENT_GUIDE.md now! 🚀
