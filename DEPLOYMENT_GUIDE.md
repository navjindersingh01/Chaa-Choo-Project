# Chaa Choo - Production Deployment Guide

## Prerequisites

- Hostinger VPS with Ubuntu 22.04 LTS or later
- Root or sudo access
- Your personal domain registered and pointing to VPS IP
- SSH access to your VPS

## Quick Start (Automated)

```bash
# 1. Upload the project to your VPS
scp -r ~/chaa-choo root@your_vps_ip:/home/

# 2. SSH into your VPS
ssh root@your_vps_ip

# 3. Run the deployment script
cd /home/chaa-choo
bash deploy.sh
```

## Manual Deployment Steps

### Step 1: Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    mysql-server nginx certbot python3-certbot-nginx curl git
```

### Step 2: Create Application Directory

```bash
# Create application directory
sudo mkdir -p /home/chaa-choo
sudo chown -R www-data:www-data /home/chaa-choo
cd /home/chaa-choo
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn
```

### Step 4: Configure Environment Variables

```bash
# Copy and edit production environment file
cp .env.production .env
nano .env

# Important: Update these values:
# - DB_PASSWORD: Set a strong password
# - SECRET_KEY: Generate a secure key: python3 -c 'import secrets; print(secrets.token_hex(32))'
# - DOMAIN: Your actual domain name
```

### Step 5: Setup MySQL Database

```bash
# Login to MySQL
mysql -u root -p

# Create database and user
CREATE USER 'cafe_user'@'localhost' IDENTIFIED BY 'your_strong_password';
CREATE DATABASE cafe_ca3;
GRANT ALL PRIVILEGES ON cafe_ca3.* TO 'cafe_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Import database schema (if you have a backup)
mysql -u cafe_user -p cafe_ca3 < backup.sql
```

### Step 6: Setup Gunicorn

```bash
# Test Gunicorn configuration
gunicorn --config gunicorn_config.py wsgi:app

# Create systemd service
sudo cp chaa-choo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chaa-choo.service
sudo systemctl start chaa-choo.service
```

### Step 7: Setup Nginx

```bash
# Copy Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/chaa-choo
sudo ln -s /etc/nginx/sites-available/chaa-choo /etc/nginx/sites-enabled/

# Update domain in Nginx config
sudo sed -i 's/yourdomain.com/your-actual-domain.com/g' /etc/nginx/sites-available/chaa-choo

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 8: Setup SSL/HTTPS with Let's Encrypt

```bash
# Generate SSL certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Update Nginx config with certificate paths
# The paths should be:
# - /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# - /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Restart Nginx
sudo systemctl reload nginx
```

### Step 9: Setup Automatic Certificate Renewal

```bash
# Create renewal service
sudo crontab -e

# Add this line:
0 3 * * * /usr/bin/certbot renew --quiet && /usr/sbin/systemctl reload nginx
```

### Step 10: Setup Firewall

```bash
# Enable UFW firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

## Verification

```bash
# Check if application is running
systemctl status chaa-choo

# Check Nginx status
systemctl status nginx

# View application logs
journalctl -u chaa-choo -f

# Test your domain
curl https://yourdomain.com
```

## Common Issues & Solutions

### 1. Database Connection Error
```bash
# Check MySQL is running
systemctl status mysql

# Verify credentials in .env
cat .env | grep DB_

# Test connection
mysql -u cafe_user -p -h localhost
```

### 2. Permission Denied Errors
```bash
# Fix ownership
sudo chown -R www-data:www-data /home/chaa-choo
sudo chmod -R 755 /home/chaa-choo
```

### 3. Port Already in Use
```bash
# Check what's using port 5000
lsof -i :5000

# Kill the process if needed
sudo kill -9 <PID>
```

### 4. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Check Nginx SSL configuration
sudo nginx -T
```

## Performance Optimization

### Enable Gzip Compression (in Nginx)
- Already configured in nginx.conf ✓

### Enable Caching
- Static files are cached for 30 days ✓
- Consider using Redis for session caching

### Database Optimization
```bash
# Backup your database regularly
mysqldump -u cafe_user -p cafe_ca3 > backup_$(date +%Y%m%d_%H%M%S).sql

# Schedule automated backups
0 2 * * * /usr/bin/mysqldump -u cafe_user -p'password' cafe_ca3 > /home/backups/cafe_ca3_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

## Security Hardening

### 1. Setup Fail2Ban
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. SSH Hardening
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Change default port (optional, but recommended)
Port 2222

# Disable root login
PermitRootLogin no

# Restart SSH
sudo systemctl restart ssh
```

### 3. Regular Updates
```bash
# Enable automatic security updates
sudo apt install unattended-upgrades
sudo systemctl enable unattended-upgrades
```

## Maintenance

### Viewing Logs
```bash
# Application logs
journalctl -u chaa-choo -f

# Nginx logs
tail -f /var/log/nginx/chaa-choo-access.log
tail -f /var/log/nginx/chaa-choo-error.log

# Gunicorn logs
tail -f /var/log/gunicorn/error.log
```

### Database Backup
```bash
# Manual backup
mysqldump -u cafe_user -p cafe_ca3 > cafe_ca3_backup.sql

# Restore from backup
mysql -u cafe_user -p cafe_ca3 < cafe_ca3_backup.sql
```

### Restarting Services
```bash
# Restart application
sudo systemctl restart chaa-choo

# Reload Nginx (no downtime)
sudo systemctl reload nginx

# Restart MySQL
sudo systemctl restart mysql
```

## Monitoring

### Setup Health Check
```bash
# Create a simple health check endpoint
curl -s https://yourdomain.com/health
```

### Monitor Resource Usage
```bash
# CPU and Memory
top

# Disk usage
df -h

# Specific application
ps aux | grep gunicorn
```

## Scaling (Future)

When you need to handle more traffic:

1. **Load Balancing**: Setup Nginx upstream with multiple Gunicorn workers
2. **Caching**: Implement Redis for session and cache storage
3. **CDN**: Use Cloudflare or similar for static asset delivery
4. **Database**: Consider database replication or clustering

## Support & Troubleshooting

For issues, check:
1. Application logs: `journalctl -u chaa-choo -f`
2. Nginx logs: `/var/log/nginx/chaa-choo-error.log`
3. MySQL logs: `/var/log/mysql/error.log`

## Important Notes

⚠️ **Security**: 
- Always use HTTPS in production
- Keep SECRET_KEY secure and unique
- Use strong database passwords
- Regularly update all packages
- Setup automated backups

⚠️ **Performance**:
- Monitor resource usage regularly
- Optimize database queries
- Use caching effectively
- Consider using a CDN for static files

⚠️ **Maintenance**:
- Test SSL renewal before expiration
- Keep backups in a separate location
- Monitor disk space
- Keep application code updated
